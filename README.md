# PastePacket

> 把长日志、控制台输出、Agent 回报、截图和普通文件，快速整理成可发送、可拖入 GPT 的独立文件包。

PastePacket is a small local desktop tool for packaging long logs, console output, AI agent reports, screenshots, WeChat images, and ordinary files into clean standalone packets before sending them to GPT / ChatGPT, teammates, or other tools.

It is designed to reduce context pollution, version confusion, long-text truncation, and messy file naming during AI-assisted debugging and collaboration.

---

## 中文简介

PastePacket 是一个本地小工具，用于把 Unity Console、终端日志、构建报错、Agent 回报、微信图片、截图和普通文件快速整理成独立文件包，再拖入 GPT / ChatGPT 或通过微信发送给别人。

它不是 AI 工具，也不调用任何 API。它只做一件事：

```text
把复杂输入先打包成边界清楚、命名清楚、可传递的本地文件。
```

---

## What PastePacket Solves / 解决什么问题

### 1. 避免 GPT 上下文污染

当你把复杂控制台日志直接粘进 GPT 时，GPT 可能会把不同轮次的日志误认为同一个文件、同一个版本或同一段上下文。

PastePacket 会把每次日志生成一个独立 TXT 文件，例如：

```text
LOG_483927.txt
```

这样每次日志都有清楚边界，减少旧路径、旧错误、旧缓存、旧附件对后续判断的污染。

---

### 2. 避免超长文本复制粘贴被截断

超长 Console、构建日志、Agent 回报直接粘贴进聊天工具时，经常会出现：

```text
中途粘贴失败
末尾信息不全
最后几行关键报错丢失
```

PastePacket 会先把完整内容写入 TXT 文件，再作为文件传递，更适合保存完整长输出。

---

### 3. 让超长文本可以通过微信发送

有些超长文本直接复制到微信里发不出去，或者发送体验很差。

PastePacket 可以把这些内容转成 TXT 文件：

```text
长文本 → TXT 文件 → 微信发送
```

这样更适合把日志、报错、排查信息发给同事或团队成员。

---

### 4. 微信图片、截图下载后快速改名整理

微信图片、截图、缓存文件下载后，文件名常常不可读。

PastePacket 支持把图片或普通文件拖入窗口：

```text
拖入图片 → 复制到输出目录 → 按命名规则改名 → 保留扩展名
```

原文件不会被修改。

---

## Core Features / 核心功能

- 粘贴长文本，生成 `.txt` 日志包。
- 拖入真实本地文件或图片，复制到输出目录并重命名。
- 保留原文件，不修改源文件。
- 保留文件扩展名。
- 默认使用稳定输出目录：
  - Windows 有 D 盘时：`D:\GPT_LogPackets`
  - 否则：`~/PastePacket_LogPackets`
- 支持用户自定义输出目录。
- 三种命名方式：
  - 递增序号
  - 自定义名称
  - 随机短码
- 最近文件列表。
- 可从最近文件列表拖出真实文件到 GPT / 浏览器 / 文件管理器。
- 支持超长文本按大小拆分。
- 支持自定义 TXT 模板。
- 模板框默认留空；留空时使用内置默认模板。
- 本地运行。
- 不联网。
- 不调用 OpenAI API。
- 不执行日志内容。

---

## Quick Start / 快速开始

### Option 1: Use the EXE / 使用 EXE

Download `PastePacket.exe` from Releases and run it directly.

On Windows, the app is packaged in windowed mode, so no black console window should appear.

### Option 2: Run from Source / 从源码运行

Install dependency:

```bash
pip install PySide6
```

Run:

```bash
python PastePacket.py
```

If `python` is not available on Windows, use:

```bash
py PastePacket.py
```

---

## Basic Usage / 基本用法

### A. Generate a TXT packet from long text

1. Copy Unity Console output, terminal logs, build errors, or Agent reports.
2. Paste into the main text area.
3. Click **生成 TXT 文件**.
4. Find the generated file in the recent file list.
5. Drag the `.txt` file into GPT / ChatGPT, or send it through WeChat.

Workflow:

```text
复制日志 → 粘贴到 PastePacket → 生成 TXT → 拖入 GPT / 发送微信
```

---

### B. Import and rename files

You can also drag real local files into PastePacket, such as:

- screenshots
- WeChat images
- `.log` files
- `.txt` files
- source code files
- ordinary documents

PastePacket will:

```text
copy → rename → preserve extension
```

It will not modify the original file.

---

## Naming Modes / 命名方式

PastePacket supports three mutually exclusive naming modes.

### 1. Incremental Sequence / 递增序号

Examples:

```text
LOG_001.txt
LOG_002.txt
LOG_003.png
```

Best for processing a continuous batch of related logs or files.

---

### 2. Custom Filename / 自定义名称

Examples:

```text
Unity_Build_Error.txt
ACB_Agent_Report.txt
WeChat_Screenshot.txt
```

If the target file already exists, PastePacket automatically appends a suffix such as:

```text
_2
_3
```

---

### 3. Random Short Code / 随机短码

Examples:

```text
LOG_483927.txt
LOG_293104.png
```

Best for high-frequency temporary GPT log packets.

This is the recommended default mode.

---

## Output Directory / 输出目录

PastePacket avoids unstable temporary folders by default.

On Windows, it prefers:

```text
D:\GPT_LogPackets
```

If the D drive does not exist, it falls back to:

```text
~/PastePacket_LogPackets
```

You can choose a custom output directory in the app.

Recommended to avoid:

```text
Temp
Downloads
Desktop
OneDrive
cloud-synced folders
```

These folders may be cleaned, synced, locked, or monitored by security software.

---

## TXT Packet Template / TXT 模板

PastePacket has a built-in default template for generated TXT files.

The default template includes fields such as:

```text
LOG_PACKET_ID
CREATED_AT
SOURCE
BOUNDARY
RAW CONTENT START
RAW CONTENT END
```

Its purpose is to tell GPT that the file is:

```text
one-time diagnostic evidence
not source code
not a design document
not a version baseline
not long-term project memory
```

### Custom Template

The template editor is empty by default.

If left empty, PastePacket uses the internal default template.

If you define a custom template, it must contain:

```text
{raw_content}
```

Supported placeholders:

```text
{packet_id}
{created_at}
{source}
{file_name}
{part_index}
{part_total}
{raw_content}
```

---

## Long Text Splitting / 超长文本拆分

PastePacket supports splitting very long text into multiple TXT files.

You can choose:

```text
B
KB
MB
```

Example output:

```text
LOG_001_part01.txt
LOG_001_part02.txt
LOG_001_part03.txt
```

This is useful when one log is too large to send or upload as a single file.

---

## Safety / 安全边界

PastePacket is a local packaging tool, not an execution tool.

It does **not**:

- upload files
- connect to cloud services
- call OpenAI API
- execute pasted logs
- execute imported files
- modify original files
- scan unrelated folders
- auto-start with Windows
- run as a background service

For imported files, it only performs:

```text
copy → rename → preserve extension
```

---

## Build from Source / 从源码打包

Install dependencies:

```bash
py -m pip install PySide6 pyinstaller
```

Build a no-console Windows EXE:

```bash
py -m PyInstaller --noconfirm --clean --onefile --windowed --name PastePacket PastePacket.py
```

The output will be:

```text
dist/PastePacket.exe
```

The `--windowed` flag prevents a black console window from appearing when the app starts.

---

## Recommended Use Cases / 推荐使用场景

PastePacket is useful for:

- Unity debugging
- GPT-assisted coding
- AI Agent report packaging
- build error packaging
- terminal log cleanup
- sending long logs through WeChat
- renaming WeChat images and screenshots
- preparing files before sending them to GPT
- separating temporary diagnostic evidence from long-term project context

---

## Project Status / 项目状态

Current version:

```text
v0.4.6 compact UI
```

This version focuses on:

- stable output path
- compact UI
- three clear naming modes
- random short-code naming
- drag-and-drop file packaging
- recent file drag-out
- no-console Windows packaging

---

## Roadmap / 后续计划

Possible future improvements:

- GitHub Releases
- app icon
- installer
- Quicker action version
- AutoHotkey helper
- portable settings
- file type presets
- one-click packet summary
- better drag-to-GPT workflow
- screenshots and demo video
- English-only README version

---

## License

Recommended:

```text
MIT License
```

License file to be added.
