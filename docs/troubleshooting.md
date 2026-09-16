# 故障排查

## 没有中文或主题没变化

1. 保存工作并重启电脑，然后登录。
2. 按 **Ctrl + 空格** 切到 Rime，输入 `nihao`。
3. 检查输入法进程与默认框架：

```bash
pgrep -a fcitx5
im-config -m
```

主题请在 **Fcitx5 配置 → 附加组件 → 经典用户界面** 中选择“清爽浅蓝”。

## 安装后黑屏

目前收到一例 Ubuntu 22.04 反馈：安装后黑屏，强制重启后恢复。具体发生步骤和日志待补充。

初版安装末尾的 `fcitx5-remote -r` 可能通过 D-Bus 启动尚未运行的输入法。当前版本已移除此调用，改为重启电脑并登录后加载。**这是减少当前会话干预的改进，黑屏原因仍待确认。**

反馈时请提供：

- 黑屏发生在安装中、安装结束后，还是点击“注销”或重启登录后。
- 大致时间、安装终端最后显示的内容、鼠标是否还能动。
- 重启后输入法是否正常，以及下面的系统信息和日志。

以下命令只读取信息：

```bash
cat /etc/os-release
echo "$XDG_CURRENT_DESKTOP / $XDG_SESSION_TYPE"
lspci -nnk | grep -A3 -Ei 'VGA|3D|Display'
journalctl --list-boots --no-pager
sudo journalctl -b -1 --no-pager -o short-iso -g 'gnome-shell|gdm|mutter|fcitx|ibus|segfault|oom|Out of memory|NVRM|Xid|GPU HANG' | tail -n 150
```

`-b -1` 查看上一次启动；如果之后又重启过，请按启动列表选择故障对应的编号。若显示没有历史日志，请一并说明。发送前可遮掉用户名和主机名。

无需为了收集信息再次触发黑屏。恢复原输入法的方法见[首页](../README.md#备份与恢复)。
