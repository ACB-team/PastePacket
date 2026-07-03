# PastePacket v0.4.6 打包说明

## 推荐步骤

1. 解压到稳定目录，例如：

```text
D:\data\GameDev\Quicker_tools\paste\PastePacket_v046_build_package_v2
```

2. 双击：

```text
build_no_console.bat
```

或在 PowerShell 中运行：

```powershell
.\build_no_console.bat
```

3. 成功后输出：

```text
dist\PastePacket.exe
```

该 exe 使用 PyInstaller `--windowed`，正常双击不会显示黑色命令行窗口。

## 如果失败

这版脚本会生成完整日志：

```text
build.log
```

请把 `build.log` 发给排查，不要只发最后一行 `[ERROR] Build failed`。

## 说明

- 打包脚本会创建本目录下 `.venv`，避免污染全局 Python。
- 第一次打包需要联网安装 PySide6 和 PyInstaller。
- 如果网络访问 pip 很慢，可先配置国内镜像，或手动安装依赖。
