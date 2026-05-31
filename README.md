# PastePacket｜粘贴包

**PastePacket（粘贴包）** 是一个本地优先的小工具，用于把粘贴文本、调试日志、截图和拖入文件整理成干净、可分享的文件包。

它不是只服务于 GPT 或 AI 对话，但尤其适合这些场景：你需要把 Unity Console、程序报错、Agent 回报、微信图片、截图或临时文件整理成清晰的 TXT / 文件附件，再发送给 AI、同事或其他工具，而不是直接把一大段内容粘进聊天窗口里。尤其避免了因为复制文本附件名称相同而引起的缓存命中，gpt读不到新的文件的问题

---

## 主要功能

- 粘贴长文本并生成干净的 TXT 文件包；
- 支持把真实路径文件拖入程序，自动复制并重命名；
- 支持图片、截图、日志、代码、文档等普通文件；
- 保留原文件扩展名；
- 不修改原文件，只复制到输出目录；
- 支持规则文件名、自定义文件名、随机码文件名；
- 支持自定义 TXT 文件模板；
- 支持超长文本按大小拆分；
- 支持窗口置顶；
- 支持无黑框运行源码版；
- 支持打包为无黑框 Windows EXE。

---

## 典型使用场景

### 1. 整理 AI 对话输入

当你需要把长日志、报错、测试回报发给 ChatGPT、Claude、Gemini 或其他 AI 工具时，可以先用 PastePacket 生成独立 TXT 文件，再作为附件上传。

这样可以减少以下问题：

- 直接粘贴污染对话上下文；
- 多段日志被 AI 误认为同一个文件；
- 文件边界不清；
- 长文本难以复查；
- 微信图片或截图文件名混乱。

### 2. 打包调试日志

适用于：

- Unity Console 日志；
- Python / Node / PowerShell 报错；
- Agent 执行回报；
- 构建失败日志；
- 测试输出；
- 临时诊断文本。

### 3. 清理微信图片和截图文件名

微信、截图工具或临时下载文件经常带有混乱文件名。你可以把真实路径文件拖入 PastePacket，让它复制到输出目录并按规则重命名。

---

## 安装与运行

### 环境要求

- Windows
- Python 3.10+
- PySide6

### 第一次使用

解压源码包后，先运行：

```bat
install_dependencies.bat
```

该脚本会安装 PySide6。

### 无黑框运行

推荐双击：

```text
run_no_console.vbs
```

如果你需要查看报错或调试信息，可以运行：

```text
run_debug_console.bat
```

---

## 打包为 EXE

双击：

```text
build_exe_windowed.bat
```

打包完成后，生成的程序位于：

```text
dist\PastePacketQt.exe
```

该 EXE 使用 `--windowed` 参数打包，正常情况下不会显示命令提示符黑框。

---

## 使用说明

### 生成 TXT 文件包

1. 打开 PastePacket；
2. 将日志、报错或长文本粘贴到主输入框；
3. 点击“生成 TXT 文件”；
4. 到输出目录中找到生成的 TXT 文件；
5. 将该文件发送给 AI、同事或其他工具。

### 拖入文件并重命名

1. 将图片、截图、日志、文档等真实路径文件拖入程序；
2. PastePacket 会复制文件到输出目录；
3. 文件会按当前命名规则自动重命名；
4. 原文件不会被修改。

---

## 文件名模式

PastePacket 支持三种文件名模式：

### 规则文件名

例如：

```text
LOG_001.txt
LOG_002.png
LOG_003.docx
```

适合日常连续整理。

### 自定义文件名

例如：

```text
Unity_Build_Error.txt
WeChat_Screenshot.png
```

适合单次明确命名。

### 随机码文件名

例如：

```text
LOG_483927.txt
```

适合避免重名或快速生成临时包。

---

## 本地优先与隐私

PastePacket 是本地工具：

- 不联网；
- 不上传文件；
- 不需要账号；
- 不修改原文件；
- 不执行日志内容；
- 不读取文件内容用于分析；
- 只是将文本写入 TXT，或将文件复制并重命名。

---

## 当前边界

当前版本主要面向 Windows 桌面使用。

文件拖入功能仅处理**真实本地文件路径**。如果某些应用拖出的对象不是实际文件路径，可能无法识别。遇到这种情况，可以先将文件保存到本地，再拖入 PastePacket。

---

## 项目定位

PastePacket 的目标不是做大型文件管理器，也不是替代专业笔记、网盘或日志平台。它解决的是一个更小但很常见的问题：

> 把临时文本、日志、截图和文件快速整理成边界清晰、名称干净、方便交接的文件包。

它尤其适合 AI 对话、调试协作、临时文件交接和轻量化工作流。

---

## License

MIT License

---

# PastePacket

**PastePacket** is a local-first utility for turning pasted text, debugging logs, screenshots, and dragged files into clean, shareable packets.

It is not limited to GPT or AI workflows, but it is especially useful when you need to prepare logs, screenshots, agent reports, or temporary files before sending them to an AI assistant, a teammate, or another tool.

> The default interface language is **Simplified Chinese**.

---

## Features

- Paste long text and generate clean TXT packets;
- Drag real-path files into the app and copy-rename them automatically;
- Support images, screenshots, logs, code files, documents, and regular files;
- Preserve original file extensions;
- Keep original files unchanged;
- Support rule-based filenames, custom filenames, and random-code filenames;
- Support custom TXT packet templates;
- Support optional long-text splitting;
- Support always-on-top window mode;
- Support no-console source launcher;
- Support building a no-console Windows EXE.

---

## Typical Use Cases

### 1. Preparing AI Chat Inputs

When sending long logs, errors, test reports, or agent outputs to ChatGPT, Claude, Gemini, or other AI tools, you can first turn them into clean TXT attachments.

This helps reduce problems such as:

- Polluting the chat context with raw pasted text;
- Multiple logs being confused as one file;
- Unclear content boundaries;
- Hard-to-review long text;
- Messy filenames from screenshots or messaging apps.

### 2. Packaging Debug Logs

Useful for:

- Unity Console logs;
- Python / Node / PowerShell errors;
- Agent execution reports;
- Build failure logs;
- Test outputs;
- Temporary diagnostic text.

### 3. Cleaning Screenshot and File Names

Screenshots, WeChat images, or temporary downloaded files often have messy filenames. PastePacket can copy them into an output folder and rename them with a clean naming rule.

---

## Installation and Run

### Requirements

- Windows
- Python 3.10+
- PySide6

### First Run

After extracting the source package, run:

```bat
install_dependencies.bat
```

This installs PySide6.

### Run Without Console Window

Recommended:

```text
run_no_console.vbs
```

For debugging or checking errors, run:

```text
run_debug_console.bat
```

---

## Build EXE

Run:

```text
build_exe_windowed.bat
```

The generated executable will be located at:

```text
dist\PastePacketQt.exe
```

The EXE is built with the `--windowed` option, so it should not show a command prompt window.

---

## How to Use

### Generate a TXT Packet

1. Open PastePacket;
2. Paste logs, errors, or long text into the main input area;
3. Click “生成 TXT 文件”;
4. Find the generated TXT file in the output folder;
5. Send the file to an AI assistant, teammate, or another tool.

### Drag and Rename Files

1. Drag a real-path file into PastePacket;
2. PastePacket copies it to the output folder;
3. The copied file is renamed according to the current naming rule;
4. The original file remains unchanged.

---

## Filename Modes

PastePacket supports three filename modes:

### Rule-based Filename

Example:

```text
LOG_001.txt
LOG_002.png
LOG_003.docx
```

Good for daily sequential packaging.

### Custom Filename

Example:

```text
Unity_Build_Error.txt
WeChat_Screenshot.png
```

Good for explicit one-off naming.

### Random-code Filename

Example:

```text
LOG_483927.txt
```

Good for quick temporary packets and avoiding name conflicts.

---

## Local-first and Privacy

PastePacket is a local utility:

- No network access;
- No file upload;
- No account required;
- Does not modify original files;
- Does not execute log content;
- Does not analyze file contents;
- Only writes pasted text into TXT files or copy-renames selected files.

---

## Current Scope

The current version is mainly designed for Windows desktop use.

Drag-and-drop only works with **real local file paths**. If an app provides a non-file drag object instead of a real file path, PastePacket may not recognize it. In that case, save the file locally first and then drag it into PastePacket.

---

## Project Positioning

PastePacket is not a large file manager, a note-taking app, or a cloud log platform. It solves a smaller but common problem:

> Quickly turning temporary text, logs, screenshots, and files into clean, well-bounded, handoff-ready packets.

It is especially useful for AI chat, debugging collaboration, temporary file handoff, and lightweight workflows.

---

## License

MIT License
