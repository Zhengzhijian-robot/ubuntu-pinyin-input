# 开发与测试

## 自动测试

在项目目录执行：

```bash
/usr/bin/python3 -m unittest discover -s tests -v
bash -n install.sh restore.sh
bash install.sh --dry-run
```

测试使用临时目录和模拟命令，覆盖环境检测、软件包选择、备份恢复、个人数据保留，以及安装完成后不调用即时重载。真实桌面的输入与重启登录需另行验证。

## 重新生成主题图片

安装 `python3-cairo` 后执行：

```bash
/usr/bin/python3 tools/generate_theme.py
```

主题文件位于 `themes/clean-blue/`，输入设置位于 `config/`，安装与恢复逻辑位于 `tools/setup.py`。

## 安装流程

检测系统与依赖 → 安装软件 → 下载并编译词库 → 备份配置 → 应用配置 → 提示用户重启电脑。

安装结束后由用户保存工作并重启电脑，在新会话中加载输入法。修改此流程时，需要检查首次安装、已有 Fcitx5、安装失败回滚和恢复四种情况。
