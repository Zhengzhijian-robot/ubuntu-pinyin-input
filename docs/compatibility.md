# 兼容性与版本

## 环境支持

| 环境 | 安装方式 | 验证情况 |
| --- | --- | --- |
| Ubuntu 22.04 / GNOME / X11 | 自动安装 | 配置在 22.04.5 使用验证 |
| Ubuntu 24.04 及以上 / GNOME / X11 | 自动检测组件并安装 | 待桌面实测 |
| Ubuntu 22.04 及以上 / GNOME / Wayland | 自动检测组件并安装 | 待桌面实测，见下方说明 |
| 其他桌面或发行版，已有 Fcitx5 | `--theme-only` | 主题需使用经典用户界面 |

安装器检查系统、会话和软件源，在本机编译词库。缺少必要依赖时会给出提示并停止。自定义 `XDG_CONFIG_HOME` / `XDG_DATA_HOME` 目录布局暂不支持。

查看自己的桌面环境：

```bash
echo "$XDG_CURRENT_DESKTOP / $XDG_SESSION_TYPE"
```

## Wayland 与主题

蓝白主题由 Fcitx5 **Classic UI（经典用户界面）**绘制。完整安装会启用它，并禁用 Fcitx5 的 Kimpanel 界面插件。

在 GNOME Wayland 下，部分应用的候选框位置可能有偏差，GNOME Shell 搜索框可能不显示候选框。Kimpanel 可以改善部分桌面集成，但外观由它管理。

如果遇到这些问题，登录页提供 **Ubuntu on Xorg** 时，可以选择该会话再测试。仅安装主题的模式保留原有界面插件设置。

## 组件版本

| 组件 | Ubuntu 22.04.5 验证版本 |
| --- | --- |
| Fcitx5 | 5.0.14 |
| fcitx5-rime | 5.0.11 |
| librime | 1.7.3 |
| 雾凇 | `59fcb4a6bfa71e6ba4fc83af07ee55f0c5b76081` |

安装器要求 Fcitx5 ≥ 5.0.14、fcitx5-rime ≥ 5.0.11、librime-bin ≥ 1.7.3，使用当前系统软件源提供的版本。GTK2、GTK4、Qt6 接口有可用软件包时自动加入；使用 Qt6 应用需要对应接口。

各版本统一使用原生 Rime 组件和固定雾凇词库，Lua 扩展未启用。软件包版本检测与词库编译通过后，仍需在目标桌面验证输入效果。

## 验证进度

已检查本机中文候选、中英切换、主题和拼音显示，以及脚本备份恢复、环境判断、词库下载编译。全新系统的完整安装、重启登录与恢复测试待补齐。

已有一例 Ubuntu 22.04 安装后黑屏反馈，强制重启后恢复，原因待日志确认。当前脚本已取消安装末尾的即时重载；排查记录见[故障排查](troubleshooting.md)。

参考：[Fcitx5 设置](https://fcitx-im.org/wiki/Setup_Fcitx_5)、[Wayland 配置](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)、[Classic UI 配置](https://github.com/fcitx/fcitx5/blob/master/src/ui/classic/classicui.h)。
