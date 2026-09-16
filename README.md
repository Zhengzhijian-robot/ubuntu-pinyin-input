# Ubuntu 中文拼音输入法界面

基于 **Fcitx5 + Rime + 雾凇拼音** 的中文输入配置，附带 **清爽蓝白（Clean Blue）** 主题、安装与恢复脚本。

**实机验证：Ubuntu 22.04.5 · GNOME · X11。自动适配：Ubuntu 22.04 及以上的 GNOME 桌面。** 安装器检测版本、X11／Wayland 和软件源提供的组件，选择当前系统的软件包。其他版本与 Wayland 的桌面效果尚未实测，详见[兼容性说明](docs/compatibility.md)。自动安装脚本经过隔离检查；尚未做全新系统端到端安装验收。

![蓝白输入法界面示意图](docs/preview.svg)

*上图为界面示意，实际候选词随词库和个人输入习惯变化。*

## 输入体验

- 简体全拼；支持雾凇的中文、英文和中英混合词库。
- 白色圆角候选框、蓝色选中项、淡阴影，使用思源黑体系列字体。
- 上方显示正在输入的拼音，下方横排显示 7 个候选词。
- 候选汉字后不重复显示拼音注释。
- **单按左／右 Shift**：在 Rime 内切换中英；输入到一半时保留原拼音并切到英文。
- **Ctrl + 空格**：切换 Rime 和英文键盘；若处于英文键盘，先按一次回到 Rime。
- **空格**选首项，**1–7**选对应项，**F4**打开 Rime 方案选单。

## 安装前确认

```bash
cat /etc/os-release
echo "$XDG_CURRENT_DESKTOP / $XDG_SESSION_TYPE"
```

完整安装自动识别 **Ubuntu 22.04 或更高版本、GNOME、X11／Wayland**，检查软件包候选版本；依赖不满足时会在修改输入配置前停止。其他发行版和桌面可使用 `--theme-only`。Wayland 下部分原生应用的候选框位置可能不同，GNOME Shell 搜索框可能无法显示候选框；本项目不会自动切换桌面会话。

安装需要网络，以及安装系统软件时的管理员验证。以普通桌面用户运行，**不要执行 `sudo bash install.sh`**。

## 下载并安装

在 Ubuntu 终端执行：

```bash
git clone https://github.com/Zhengzhijian-robot/ubuntu-pinyin-input.git
cd ubuntu-pinyin-input

# 可选：先查看将执行的操作，不修改任何配置
bash install.sh --dry-run

# 安装组件、下载固定版本词库、部署配置和主题
bash install.sh
```

如果缺少 Git，先执行 `sudo apt install git`。若 apt 提示找不到软件包，可先执行 `sudo apt update`，并确认启用了 Ubuntu 的 Universe 软件源。

安装完成后，**保存工作，手动注销并重新登录**。锁屏不等于注销。输入 `nihao`，应看到“你好”等候选词；再试 Shift 切换英文。

### 安装会做什么？

1. 检查系统版本、桌面、会话类型及软件源候选版本；有 GTK4／Qt6 输入模块时自动加入。
2. 从 Ubuntu 软件源安装 Fcitx5、Rime、GTK/Qt 输入接口和字体。
3. 下载并编译固定提交的雾凇词库，成功后才修改输入法配置。
4. 备份即将修改的配置、已有 Rime 目录和 GNOME 输入源。
5. 应用主题、全拼方案、兼容设置及快捷键；使用系统提供的 `im-config` 配置登录启动和输入接口。启用 Classic UI、禁用 Fcitx5 的 Kimpanel 界面插件，使蓝白主题生效；新版的自动深色主题与强调色跟随也关闭。
6. 保留 GNOME 中的键盘布局，移除 IBus 引擎入口，避免重复切换。

不会卸载 IBus，不会自动注销。已有 Rime 用户学习数据库和 `custom_phrase.txt` 会保留；同名方案、主题和相关设置会更新，原内容可从备份恢复。

## 已有 Fcitx5，只想换蓝白界面

```bash
bash install.sh --theme-only
fcitx5-remote -r
```

此模式只安装主题、调整候选框字体和排列，不安装系统软件，也不更换输入引擎、词库或快捷键。其他 Ubuntu 版本可尝试，但本项目未逐一验证；使用 GNOME Kimpanel 等界面时，外观可能由桌面扩展管理，而不是这套 Classic UI 主题。

## 恢复原输入法

安装会打印本次备份路径，形式为：

```text
~/.local/share/ubuntu-pinyin-input/backups/时间戳/
```

使用实际路径执行：

```bash
bash restore.sh ~/.local/share/ubuntu-pinyin-input/backups/你的时间戳
```

然后注销、重新登录。恢复的是这次安装前的配置与输入源，不会一律强制改成 IBus，也不会卸载共享软件包。安装后新增的配置、短语和学习数据会移入该备份的 `after-restore-*` 子目录，可另行找回。多次安装应从最新备份开始逐次恢复。

## 版本与功能边界

| 组件 | 本机验证版本 |
| --- | --- |
| Ubuntu / 桌面 | 22.04.5 / GNOME / X11 |
| Fcitx5 | 5.0.14 |
| fcitx5-rime | 5.0.11 |
| librime | 1.7.3 |
| 雾凇词库 | 固定提交 `59fcb4a6bfa71e6ba4fc83af07ee55f0c5b76081` |

各系统统一使用这套 **原生组件兼容配置**（以 Ubuntu 22.04 为基线）：保留雾凇词库与原生拼音、英文翻译器，禁用不兼容的 Lua 处理器／翻译器／过滤器。因此不能把上游新版的计算器、日期命令、Lua 辅码、错音提示等扩展都视为已支持；也未安装额外语法模型。用户词频仍会随使用学习。

输入法词库不随本仓库打包，安装时从[雾凇官方仓库](https://github.com/iDvel/rime-ice)获取指定提交。本仓库不包含作者个人输入历史、用户词库、电脑备份、密码或机器人项目文件。

## 常见问题

- **主题没变化**：确认 Fcitx5 正在运行，在“配置 → 附加组件 → 经典用户界面”中选择“清爽浅蓝”；重新加载或注销登录。
- **没有中文／仍是旧输入法**：先确认完成了注销登录，再检查 `im-config -m`、`pgrep -a fcitx5`，按 Ctrl + 空格切到 Rime。
- **Ubuntu 24.04 或更高版本**：直接运行同一安装命令，脚本会检测当前软件源和会话；不安装 Ubuntu 22.04 的旧软件包。自动适配不等于各版本都通过了桌面验收。
- **下载词库失败**：检查 GitHub 网络连接后重试。词库下载和编译在配置切换前完成。
- **字体／大小不喜欢**：在 Fcitx5 的经典用户界面设置里调整字体，默认 `Noto Sans CJK SC 13`。

## 开发与来源

```bash
# 不改动真实桌面配置的自动检查
/usr/bin/python3 -m unittest discover -s tests -v

# 重新生成原创主题 PNG，需要 python3-cairo；正常安装不需要运行
/usr/bin/python3 tools/generate_theme.py
```

安装脚本、配置和主题按 [GPL-3.0](LICENSE) 发布。基于 Fcitx5、Rime、雾凇拼音，来源与第三方许可证说明见 [THIRD_PARTY.md](THIRD_PARTY.md)。这是社区配置方案，与搜狗、豆包没有关联。
