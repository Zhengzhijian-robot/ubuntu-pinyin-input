# Ubuntu 中文拼音输入法界面

为 Ubuntu 配好 **Fcitx5 + Rime + 雾凇拼音**：蓝白候选框、上方拼音、Shift 中英切换。

![清爽蓝白输入法界面示意](docs/preview.svg)

*界面示意图；候选词会随输入和使用习惯变化。*

## 适用系统

**Ubuntu 22.04 及以上 · GNOME 桌面。** 安装脚本自动检测系统，选择软件源中的组件。

配置已在 **Ubuntu 22.04.5 / X11** 使用验证。其他版本和 Wayland 的实测进度见[兼容性说明](docs/compatibility.md)。

## 安装

打开终端，依次执行。首次安装需要联网，安装软件时按提示输入系统密码。

```bash
# 已安装 Git 可跳过前两行
sudo apt update
sudo apt install git

git clone https://github.com/Zhengzhijian-robot/ubuntu-pinyin-input.git
cd ubuntu-pinyin-input
bash install.sh
```

以普通用户运行 `bash install.sh`，不要在它前面加 `sudo`。想先查看安装计划，可执行 `bash install.sh --dry-run`。

## 安装完成后，请保存工作并重启电脑

> **保存工作 → 桌面右上角电源菜单 → 重新启动。**
>
> 重启并登录后输入 `nihao`，看到“你好”候选词就可以开始使用了。

## 怎么用

默认上方显示拼音，下方横排 **7 个汉字候选**，汉字后不重复标注拼音。

| 按键 | 功能 |
| --- | --- |
| **Shift** | 中英切换；正在输入时，先提交原拼音再切到英文 |
| **Ctrl + 空格** | 切换 Rime 和英文键盘 |
| **空格** | 选择第一个候选词 |
| **1–7** | 选择对应候选词 |
| **F4** | 打开 Rime 方案选单 |

字体和大小可在 **Fcitx5 配置 → 附加组件 → 经典用户界面** 中调整，默认 `Noto Sans CJK SC 13`。

## 已有 Fcitx5，只换主题

在项目目录执行：

```bash
bash install.sh --theme-only
```

重启电脑后生效。此模式调整蓝白主题、字体和横排布局，保留现有输入引擎、词库和快捷键。主题由 Fcitx5 的“经典用户界面”显示。

## 备份与恢复

安装前会备份输入法配置，保留已有学习词库和自定义短语。完整安装会更新同名配置、设 Fcitx5 为默认输入框架，并将 GNOME 输入源整理为键盘布局。

安装结束会显示一条恢复命令，也可以按实际备份目录执行：

```bash
bash restore.sh ~/.local/share/ubuntu-pinyin-input/backups/你的时间戳
```

恢复后请保存工作并重启电脑。安装后新增的学习数据保存在该备份的 `after-restore-*` 目录；多次安装请从最新备份开始恢复。系统软件包会保留。

## 遇到问题

| 情况 | 处理方法 |
| --- | --- |
| 没有中文 | 重启电脑并登录，再按 **Ctrl + 空格** 切到 Rime |
| 主题没变化 | 在“经典用户界面”中选择 **清爽浅蓝**；使用 Kimpanel 的用户见[兼容性说明](docs/compatibility.md) |
| 提示找不到软件包 | 执行 `sudo apt update`，检查 Ubuntu 是否启用了 Universe 软件源 |
| 词库下载失败 | 检查 GitHub 网络连接后重新运行安装命令 |
| 安装后黑屏 | 记录发生步骤和时间，按[排查说明](docs/troubleshooting.md)提供日志 |

## 项目说明

- 中文、英文及中英混合词库来自[雾凇拼音](https://github.com/iDvel/rime-ice)，安装时下载固定版本。
- 使用原生 Rime 组件，支持词频学习；计算器、日期等 Lua 扩展未启用。
- [兼容性与版本](docs/compatibility.md) · [故障排查](docs/troubleshooting.md) · [开发与测试](docs/development.md)
- 采用 [GPL-3.0](LICENSE) 许可证，感谢 Fcitx5、Rime 和雾凇拼音。完整来源见 [THIRD_PARTY.md](THIRD_PARTY.md)。
