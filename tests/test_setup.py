import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("setup", Path(__file__).parents[1] / "tools/setup.py")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class InstallationTests(unittest.TestCase):
    def test_environment_matrix(self):
        for version in ["22.04", "24.04", "26.04"]:
            for session in ["x11", "wayland"]:
                with self.subTest(version=version, session=session):
                    plan = setup.environment_plan({"ID": "ubuntu", "VERSION_ID": version},
                        {"XDG_CURRENT_DESKTOP": "ubuntu:GNOME", "XDG_SESSION_TYPE": session})
                    self.assertEqual(plan["tested"], version == "22.04" and session == "x11")
        for system, env in [({"ID": "debian", "VERSION_ID": "24.04"}, {}),
                            ({"ID": "ubuntu", "VERSION_ID": "20.04"}, {}),
                            ({"ID": "ubuntu", "VERSION_ID": "24.04"}, {"XDG_CURRENT_DESKTOP": "KDE"}),
                            ({"ID": "ubuntu", "VERSION_ID": "24.04"}, {"XDG_CURRENT_DESKTOP": "GNOME"})]:
            with self.assertRaises(RuntimeError):
                setup.environment_plan(system, env)

    def test_packages_follow_available_candidates(self):
        def candidate(args, **kwargs):
            version = "(none)" if args[-1] == "fcitx5-frontend-qt6" else "9.0"
            return subprocess.CompletedProcess(args, 0, stdout="  Candidate: " + version)
        with patch.object(setup, "run", side_effect=candidate):
            selected = setup.package_plan()
        self.assertIn("fcitx5-frontend-gtk4", selected)
        self.assertNotIn("fcitx5-frontend-qt6", selected)
        with patch.object(setup, "run", return_value=subprocess.CompletedProcess([], 0, stdout="")):
            with self.assertRaisesRegex(RuntimeError, "软件源缺少"):
                setup.package_plan()

    def test_backup_restore_preserves_later_learning(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rime = home / setup.RIME
            rime.mkdir(parents=True)
            (rime / "learning.userdb.txt").write_text("before")
            backup = setup.snapshot(home, [setup.RIME, setup.UI], "[('xkb', 'us')]")
            (rime / "learning.userdb.txt").write_text("new learning")
            setup.install_theme(home)
            manifest, archive = setup.restore_files(home, backup)
            self.assertEqual((rime / "learning.userdb.txt").read_text(), "before")
            self.assertEqual((archive / setup.RIME / "learning.userdb.txt").read_text(), "new learning")
            self.assertFalse((home / setup.UI).exists())
            self.assertEqual(manifest["gnome_sources"], "[('xkb', 'us')]")

    def test_invalid_backup_does_not_change_files(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            backup = setup.snapshot(home, [setup.UI])
            manifest = json.loads((backup / "manifest.json").read_text())
            manifest["paths"]["../../outside"] = False
            (backup / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(RuntimeError):
                setup.restore_files(home, backup)
            self.assertEqual(list(backup.glob("after-restore-*")), [])

    def test_theme_repeat_and_existing_preferences(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ui.conf"
            path.write_text("WheelForPaging=False\nTheme=old\nUseDarkTheme=True\n")
            setup.merge_ui(path)
            first = path.read_text()
            setup.merge_ui(path)
            self.assertEqual(first, path.read_text())
            self.assertIn("WheelForPaging=False", first)
            self.assertIn("Theme=clean-blue", first)
            self.assertIn("UseDarkTheme=False", first)
            self.assertIn("DarkTheme=clean-blue", first)

    def test_deploy_preserves_personal_data(self):
        with tempfile.TemporaryDirectory() as temp:
            source, dest = Path(temp) / "source", Path(temp) / "dest"
            source.mkdir()
            dest.mkdir()
            for name in ["custom_phrase.txt", "new.schema.yaml", "user.yaml", "private.userdb.txt"]:
                (source / name).write_text("upstream")
            (dest / "custom_phrase.txt").write_text("my phrase")
            (dest / "rime_ice.userdb").mkdir()
            (dest / "rime_ice.userdb/data").write_text("learned")
            setup.deploy_ice(source, dest)
            self.assertEqual((dest / "custom_phrase.txt").read_text(), "my phrase")
            self.assertEqual((dest / "rime_ice.userdb/data").read_text(), "learned")
            self.assertTrue((dest / "new.schema.yaml").exists())
            self.assertFalse((dest / "user.yaml").exists())
            self.assertFalse((dest / "private.userdb.txt").exists())

    def test_nested_symlink_stops_before_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            target = home / setup.RIME / "dicts"
            target.mkdir(parents=True)
            outside = home / "untouched"
            outside.write_text("original")
            (target / "external").symlink_to(outside)
            with self.assertRaises(RuntimeError):
                setup.check_paths(home, [setup.RIME])
            self.assertEqual(outside.read_text(), "original")

    def test_dry_run_only_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(setup, "os_release", return_value={"ID": "ubuntu", "VERSION_ID": "24.04"}), \
                 patch.dict(setup.os.environ, {"XDG_CURRENT_DESKTOP": "GNOME", "XDG_SESSION_TYPE": "wayland"}), \
                 patch.object(setup, "package_plan", return_value={"fcitx5": "5.1"}), \
                 patch.object(setup, "run") as commands:
                setup.install(argparse.Namespace(theme_only=False, dry_run=True), Path(temp))
                commands.assert_not_called()
                self.assertEqual(list(Path(temp).iterdir()), [])

    def test_install_failure_restores_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            old_config = home / ".config/fcitx5/config"
            old_config.parent.mkdir(parents=True)
            old_config.write_text("original settings")
            source = Path(temp) / "source"
            source.mkdir()
            (source / "test.schema.yaml").write_text("test")
            sources = "[('xkb', 'us'), ('ibus', 'libpinyin')]"
            commands = []

            def command(args, **kwargs):
                commands.append(args)
                if args[:2] == ["im-config", "-n"]:
                    raise subprocess.CalledProcessError(1, args)
                return subprocess.CompletedProcess(args, 0, stdout=sources)

            with patch.object(setup, "os_release", return_value={"ID": "ubuntu", "VERSION_ID": "24.04"}), \
                 patch.dict(setup.os.environ, {"XDG_CURRENT_DESKTOP": "GNOME", "XDG_SESSION_TYPE": "x11"}), \
                 patch.object(setup, "package_plan", return_value={"fcitx5": "5.1"}), \
                 patch.object(setup, "build_ice", return_value=source), \
                 patch.object(setup, "run", side_effect=command):
                with self.assertRaises(subprocess.CalledProcessError):
                    setup.install(argparse.Namespace(theme_only=False, dry_run=False), home)
            self.assertEqual(old_config.read_text(), "original settings")
            self.assertFalse((home / setup.RIME).exists())
            self.assertFalse((home / setup.THEME).exists())
            self.assertEqual(commands[-1][-1], sources)


if __name__ == "__main__":
    unittest.main()
