#!/usr/bin/env python3
"""自动适配 Ubuntu GNOME，安装统一的蓝白拼音界面。"""
import argparse
import ast
import datetime
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ICE_URL = "https://github.com/iDvel/rime-ice.git"
ICE_COMMIT = "59fcb4a6bfa71e6ba4fc83af07ee55f0c5b76081"
BACKUP_ROOT = ".local/share/ubuntu-pinyin-input/backups"
THEME = ".local/share/fcitx5/themes/clean-blue"
RIME = ".local/share/fcitx5/rime"
UI = ".config/fcitx5/conf/classicui.conf"
MANAGED = [UI, THEME, ".config/fcitx5/config", ".config/fcitx5/profile",
           ".config/fcitx5/conf/rime.conf", RIME, ".xinputrc",
           ".config/fcitx5/addon/kimpanel.conf", ".config/fcitx5/addon/classicui.conf"]
PACKAGES = ["fcitx5", "fcitx5-rime", "fcitx5-config-qt",
            "fcitx5-frontend-gtk3", "fcitx5-frontend-qt5", "librime-bin",
            "fonts-noto-cjk", "im-config", "git"]
OPTIONAL_PACKAGES = ["fcitx5-frontend-gtk2", "fcitx5-frontend-gtk4", "fcitx5-frontend-qt6"]


def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def stamp():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def show_restart_notice():
    message = "安装完成后，请保存工作并重启电脑"
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    print("\n" + "=" * 64)
    print("\033[1;36m" + message + "\033[0m" if color else message)
    print("=" * 64)
    print("保存工作 → 桌面右上角电源菜单 → 重新启动。")
    print("重启并登录后即可使用新配置。\n")


def os_release(path=Path("/etc/os-release")):
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = shlex.split(value)[0] if value else ""
    return values


def environment_plan(system, env):
    version = system.get("VERSION_ID", "")
    if (system.get("ID") != "ubuntu" or not re.fullmatch(r"\d+\.\d+", version)
            or tuple(map(int, version.split("."))) < (22, 4)):
        raise RuntimeError("完整自动适配要求 Ubuntu 22.04 或更高版本；已有 Fcitx5 可用 --theme-only。")
    if "gnome" not in env.get("XDG_CURRENT_DESKTOP", "").lower():
        raise RuntimeError("当前仅实现 GNOME 桌面的完整适配；其他桌面可用 --theme-only。")
    session = env.get("XDG_SESSION_TYPE", "")
    if session not in {"x11", "wayland"}:
        raise RuntimeError("请在 GNOME 桌面的终端运行，以识别 X11 / Wayland。")
    return {"session": session, "tested": version == "22.04" and session == "x11"}


def package_plan():
    """Select packages from this machine's apt candidates, never pin foreign builds."""
    candidates = {}
    for name in PACKAGES + OPTIONAL_PACKAGES:
        output = run(["apt-cache", "policy", name], capture_output=True,
                     env={**os.environ, "LC_ALL": "C"}).stdout
        match = re.search(r"^\s*Candidate:\s*(\S+)", output, re.MULTILINE)
        if match and match[1] != "(none)":
            candidates[name] = match[1]
    missing = [name for name in PACKAGES if name not in candidates]
    if missing:
        raise RuntimeError("软件源缺少：" + ", ".join(missing)
                           + "。请先 sudo apt update，并检查 Universe 软件源。")
    for name, minimum in [("fcitx5", "5.0.14"), ("fcitx5-rime", "5.0.11"),
                          ("librime-bin", "1.7.3")]:
        result = subprocess.run(["dpkg", "--compare-versions", candidates[name], "ge", minimum])
        if result.returncode:
            raise RuntimeError(name + " 候选版本低于所需的 " + minimum)
    return candidates


def check_paths(home, paths):
    for rel in paths:
        target = home / rel
        for part in [target, *target.parents]:
            if part == home:
                break
            if part.is_symlink():
                raise RuntimeError("目标路径包含符号链接，请先检查：" + str(part))
        if target.is_dir():
            for child in target.rglob("*"):
                if child.is_symlink():
                    raise RuntimeError("目标目录内包含符号链接，请先检查：" + str(child))


def copy_item(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target)


def snapshot(home, paths, sources=None):
    backup = home / BACKUP_ROOT / stamp()
    backup.mkdir(parents=True, mode=0o700)
    existed = {}
    for rel in paths:
        source = home / rel
        existed[rel] = source.exists() or source.is_symlink()
        if existed[rel]:
            copy_item(source, backup / "before" / rel)
    manifest = {"version": 1, "home": str(home), "paths": existed,
                "gnome_sources": sources, "ice_commit": ICE_COMMIT}
    (backup / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return backup


def restore_files(home, backup):
    manifest = json.loads((backup / "manifest.json").read_text())
    if manifest["home"] != str(home):
        raise RuntimeError("此备份属于其他用户目录，停止恢复。")
    if not set(manifest["paths"]).issubset(MANAGED):
        raise RuntimeError("备份清单包含不受管理的路径，停止恢复。")
    check_paths(home, manifest["paths"])
    for rel, existed in manifest["paths"].items():
        if existed and not ((backup / "before" / rel).exists()
                            or (backup / "before" / rel).is_symlink()):
            raise RuntimeError("备份不完整：" + rel)
    # Keep all post-install learning and edits in a separate archive, never erase them.
    archive = backup / ("after-restore-" + stamp())
    for rel, existed in manifest["paths"].items():
        target = home / rel
        if target.exists() or target.is_symlink():
            destination = archive / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(destination))
        if existed:
            copy_item(backup / "before" / rel, target)
    return manifest, archive


def merge_ui(path):
    """Change only this theme's settings; retain unrelated frontend preferences."""
    wanted = {"Theme": "clean-blue", "DarkTheme": "clean-blue", "UseDarkTheme": "False",
              "UseAccentColor": "False", "Font": '"Noto Sans CJK SC 13"',
              "MenuFont": '"Noto Sans CJK SC 11"', "PerScreenDPI": "True",
              "Vertical Candidate List": "False", "PreferTextIcon": "True"}
    lines = path.read_text().splitlines() if path.exists() else []
    result = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if not line.lstrip().startswith("#") and "=" in line and key in wanted:
            result.append(key + "=" + wanted.pop(key))
        else:
            result.append(line)
    result.extend(key + "=" + value for key, value in wanted.items())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(result) + "\n")


def install_theme(home):
    destination = home / THEME
    if destination.is_symlink():
        raise RuntimeError("主题目录是符号链接，请先检查：" + str(destination))
    shutil.copytree(ROOT / "themes/clean-blue", destination, dirs_exist_ok=True)
    merge_ui(home / UI)


def build_ice(temp):
    source = temp / "ice"
    run(["git", "init", "-q", str(source)])
    run(["git", "-C", str(source), "fetch", "--depth=1", ICE_URL, ICE_COMMIT])
    run(["git", "-C", str(source), "checkout", "-q", "--detach", "FETCH_HEAD"])
    actual = run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True).stdout.strip()
    if actual != ICE_COMMIT:
        raise RuntimeError("雾凇版本校验失败。")
    for patch in (ROOT / "config/rime").glob("*.yaml"):
        shutil.copy2(patch, source / patch.name)
    print("编译词库，首次可能需要几十秒……", flush=True)
    log = temp / "build.log"
    try:
        with log.open("w") as out:
            run(["rime_deployer", "--build", str(source), "/usr/share/rime-data",
                 str(source / "build")], stdout=out, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        tail = "\n".join(log.read_text(errors="replace").splitlines()[-25:])
        raise RuntimeError("词库编译失败，尚未修改输入配置：\n" + tail) from error
    for name in ["rime_ice.table.bin", "rime_ice.prism.bin", "rime_ice.schema.yaml",
                 "melt_eng.table.bin", "radical_pinyin.table.bin"]:
        if not (source / "build" / name).is_file():
            raise RuntimeError("词库编译结果缺失：" + name)
    return source


def deploy_ice(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or any(p.is_symlink() for p in destination.rglob("*")):
        raise RuntimeError("Rime 目录包含符号链接，停止覆盖。")
    for item in source.iterdir():
        if item.name.startswith(".") or item.name in {"installation.yaml", "user.yaml", "sync"}:
            continue
        if ".userdb" in item.name or item.name.endswith(".log"):
            continue
        target = destination / item.name
        # Preserve personal phrases, while deploying the selected schema and dictionaries.
        if item.name == "custom_phrase.txt" and target.exists():
            continue
        if target.is_symlink():
            raise RuntimeError("Rime 中存在同名符号链接，停止覆盖：" + str(target))
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def install(args, home):
    for key, default in [("XDG_CONFIG_HOME", home / ".config"),
                         ("XDG_DATA_HOME", home / ".local/share")]:
        if os.getenv(key) and Path(os.environ[key]) != default:
            raise RuntimeError("当前使用自定义 " + key + "，尚未适配此目录布局。")
    system = os_release()
    print("系统：", system.get("PRETTY_NAME"), "桌面：", os.getenv("XDG_CURRENT_DESKTOP"),
          "会话：", os.getenv("XDG_SESSION_TYPE"))
    if args.theme_only:
        if not shutil.which("fcitx5"):
            raise RuntimeError("仅安装主题需要已有 Fcitx5。")
        print("仅安装清爽蓝白主题；保留现有输入引擎、词库和快捷键。")
    else:
        plan = environment_plan(system, os.environ)
        packages = package_plan()
        print("适配方式：GNOME /", plan["session"], "；使用当前系统软件源版本。")
        print("将安装：", " ".join(name + "=" + version for name, version in packages.items()))
        if not plan["tested"]:
            print("此环境自动适配；桌面实测记录见 docs/compatibility.md。")
        if plan["session"] == "wayland":
            print("Wayland：部分应用可能出现候选框定位偏差，详见兼容性说明。")
        print("雾凇固定版本：", ICE_COMMIT)
        print("将备份并调整输入法配置；完成后请保存工作并重启电脑。")
    if args.dry_run:
        print("预览完成，没有安装软件、下载词库或写入用户配置。")
        return
    paths = MANAGED[:2] if args.theme_only else MANAGED
    check_paths(home, paths)
    if args.theme_only:
        backup = snapshot(home, paths)
        try:
            install_theme(home)
        except Exception:
            restore_files(home, backup)
            raise
        print("主题已安装，备份：", backup)
        show_restart_notice()
        return
    # Read GNOME settings before changing packages or user configuration.
    sources = run(["gsettings", "get", "org.gnome.desktop.input-sources", "sources"],
                  capture_output=True).stdout.strip()
    run(["sudo", "apt-get", "install", "-y", *packages])
    with tempfile.TemporaryDirectory(prefix="ubuntu-pinyin-input-") as temp:
        source = build_ice(Path(temp))
        backup = snapshot(home, paths, sources)
        print("配置备份：", backup, flush=True)
        try:
            install_theme(home)
            for name in ["config", "profile", "conf/rime.conf"]:
                target = home / ".config/fcitx5" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / "config/fcitx5" / name, target)
            for name, enabled in [("kimpanel", "False"), ("classicui", "True")]:
                target = home / ".config/fcitx5/addon" / (name + ".conf")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("[Addon]\nEnabled=" + enabled + "\n")
            deploy_ice(source, home / RIME)
            run(["im-config", "-n", "fcitx5"])
            # Retain all keyboard layouts; remove IBus engines to avoid competing frameworks.
            previous = ast.literal_eval(sources.removeprefix("@a(ss) "))
            layouts = [tuple(item) for item in previous if item[0] == "xkb"]
            run(["gsettings", "set", "org.gnome.desktop.input-sources", "sources",
                 repr(layouts or [("xkb", "us")])])
        except Exception:
            restore_files(home, backup)
            run(["gsettings", "set", "org.gnome.desktop.input-sources", "sources", sources])
            print("发生错误，已尝试恢复安装前配置。备份：", backup, file=sys.stderr)
            raise
    print("Shift：中英切换；Ctrl+空格：Rime/英文键盘；空格/1–7：选词。")
    print("恢复命令：bash restore.sh", shlex.quote(str(backup)))
    show_restart_notice()


def restore(args, home):
    backup = Path(args.backup).expanduser().resolve()
    if backup.parent != (home / BACKUP_ROOT).resolve():
        raise RuntimeError("请选择当前用户的 ubuntu-pinyin-input 备份目录。")
    manifest, archive = restore_files(home, backup)
    if manifest["gnome_sources"] is not None:
        run(["gsettings", "set", "org.gnome.desktop.input-sources", "sources",
             manifest["gnome_sources"]])
    print("已恢复配置；安装后的配置和学习数据保留在：", archive)
    print("软件包仍保留。请保存工作并重启电脑。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("install")
    p.add_argument("--theme-only", action="store_true", help="只安装主题，不改词库和输入法")
    p.add_argument("--dry-run", action="store_true", help="只预览，不执行安装")
    p = commands.add_parser("restore")
    p.add_argument("backup", help="安装时输出的备份目录")
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.exit(1, "请以普通桌面用户运行，不要使用 sudo bash install.sh。\n")
    try:
        (install if args.command == "install" else restore)(args, Path.home())
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as error:
        parser.exit(1, "操作未完成：" + str(error) + "\n")


if __name__ == "__main__":
    main()
