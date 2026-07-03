# -*- coding: utf-8 -*-
"""
PastePacket Maker v0.4.0 Qt Drag Edition

Purpose:
- Paste long text logs and generate TXT packets.
- Drag real-path files/images into the window, copy them to output folder, and rename them.
- Keep original files untouched.
- Preserve file extensions.

Dependency:
    pip install PySide6

Run:
    python pastepacket_qt_drag_v040.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import random
import re
import shutil
import sys
import traceback
from pathlib import Path
from typing import List, Optional

try:
    from PySide6.QtCore import Qt, QUrl, QMimeData
    from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QAction, QDrag
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QRadioButton,
        QButtonGroup,
        QSpinBox,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except Exception as exc:
    print("PySide6 is required. Install with: python -m pip install PySide6")
    print(exc)
    raise


APP_NAME = "PastePacket"
APP_VERSION = "0.4.6-compact-ui"
WORK_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = WORK_DIR / "pastepacket_qt_settings.json"
LEGACY_OUTPUT_DIR = WORK_DIR / "log_packets"


def stable_default_output_dir() -> Path:
    """Return a stable, non-temp default output directory.

    Avoid WORK_DIR/log_packets when the app is packaged as onefile because the
    executable may run from a transient unpack directory. Prefer a plain user
    data directory that is unlikely to be cleaned by temp policies.
    """
    env_dir = os.environ.get("PASTE_PACKET_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    d_root = Path("D:/")
    if d_root.exists():
        return Path("D:/GPT_LogPackets")
    return (Path.home() / "PastePacket_LogPackets").resolve()


DEFAULT_OUTPUT_DIR = stable_default_output_dir()
MAX_RECENT = 30

SAFE_FILENAME_PATTERN = re.compile(r"[^0-9A-Za-z_\-\.\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+")

DEFAULT_TEMPLATE = """LOG_PACKET_ID: {packet_id}
CREATED_AT: {created_at}
SOURCE: {source}
BOUNDARY: one-time diagnostic evidence only

以下内容仅作为一次性日志证据。
不要把它当成源码文件、设计文档、版本基线或长期项目记忆。
不要与其他日志文件合并为同一个文件。
请只分析本文档内的日志内容。

--- RAW CONTENT START ---

{raw_content}

--- RAW CONTENT END ---
"""


def now_text() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sanitize_stem(value: str, fallback: str = "LOG") -> str:
    value = (value or "").strip()
    if value.lower().endswith(".txt"):
        value = value[:-4]
    value = SAFE_FILENAME_PATTERN.sub("_", value)
    value = value.strip("._- ")
    return value or fallback


def unique_path(folder: Path, stem: str, suffix: str) -> Path:
    suffix = suffix if suffix.startswith(".") else f".{suffix}"
    path = folder / f"{stem}{suffix}"
    if not path.exists():
        return path
    for i in range(2, 10000):
        candidate = folder / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
    return folder / f"{stem}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"


def split_by_bytes(text: str, limit: int) -> List[str]:
    if limit <= 0 or len(text.encode("utf-8")) <= limit:
        return [text]
    chunks: List[str] = []
    current: List[str] = []
    current_bytes = 0
    for line in text.splitlines(keepends=True):
        b = len(line.encode("utf-8"))
        if current and current_bytes + b > limit:
            chunks.append("".join(current))
            current = []
            current_bytes = 0
        if b > limit:
            # split very long line by char
            buf = []
            buf_bytes = 0
            for ch in line:
                cb = len(ch.encode("utf-8"))
                if buf and buf_bytes + cb > limit:
                    chunks.append("".join(buf))
                    buf = []
                    buf_bytes = 0
                buf.append(ch)
                buf_bytes += cb
            current = buf
            current_bytes = buf_bytes
        else:
            current.append(line)
            current_bytes += b
    if current:
        chunks.append("".join(current))
    return chunks


def is_risky_output_dir(path: Path) -> bool:
    p = str(path).lower().replace("/", "\\")
    risky_parts = [
        "\\appdata\\local\\temp",
        "\\temp\\",
        "\\tmp\\",
        "\\desktop",
        "\\downloads",
        "\\onedrive",
        "\\dropbox",
        "\\icloud",
    ]
    return any(part in p for part in risky_parts)


def ensure_stable_output_dir(folder: Path) -> Path:
    folder = folder.expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    test_path = folder / ".pastepacket_write_test.tmp"
    try:
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("write-test")
            f.flush()
            os.fsync(f.fileno())
        if not test_path.exists() or test_path.stat().st_size <= 0:
            raise RuntimeError("输出目录写入测试失败。")
    finally:
        try:
            test_path.unlink(missing_ok=True)
        except Exception:
            pass
    return folder


def safe_write_text(path: Path, content: str) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    if not path.exists():
        raise RuntimeError("文件写入后立即消失，可能被安全软件、临时目录清理或同步策略处理。")
    if path.stat().st_size <= 0:
        raise RuntimeError("文件写入后大小为 0，可能写入失败。")


def safe_copy_file(src: Path, dst: Path) -> None:
    shutil.copy2(src, dst)
    if not dst.exists():
        raise RuntimeError(f"复制后文件不存在：{dst}")
    if src.exists() and dst.stat().st_size != src.stat().st_size:
        raise RuntimeError(f"复制后文件大小不一致：{dst}")



class DropTextEdit(QPlainTextEdit):
    def __init__(self, on_files_dropped, parent=None):
        super().__init__(parent)
        self.on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)
        self.setPlaceholderText(
            "在这里粘贴 Console / 长日志 / Agent 回报，然后点击“生成 TXT 文件”。\n\n"
            "也可以把图片、日志、文档等真实文件直接拖到这里；"
            "系统会复制改名，保留扩展名，不修改原文件。"
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    p = Path(url.toLocalFile())
                    if p.is_file():
                        files.append(p)
            if files:
                self.on_files_dropped(files)
                event.acceptProposedAction()
                return
        super().dropEvent(event)


class DropPanel(QFrame):
    def __init__(self, on_files_dropped, parent=None):
        super().__init__(parent)
        self.on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)
        self.setObjectName("DropPanel")
        self.setMinimumHeight(82)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        self.title = QLabel("拖入文件到这里")
        self.title.setObjectName("DropPanelTitle")
        self.hint = QLabel("支持微信图片、截图、日志、代码、文档等真实文件。拖入后复制到输出目录并按当前命名规则重命名；保留扩展名，原文件不修改。")
        self.hint.setObjectName("HintLabel")
        self.hint.setWordWrap(True)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        files = []
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    p = Path(url.toLocalFile())
                    if p.is_file():
                        files.append(p)
        if files:
            self.on_files_dropped(files)
            event.acceptProposedAction()
        else:
            event.ignore()


class DraggableRecentList(QListWidget):
    """Recent file list that can drag real local files to browsers/GPT."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if not item:
            return
        value = item.data(Qt.UserRole)
        if not value:
            return
        path = Path(value)
        if not path.exists():
            QMessageBox.warning(self, "文件不存在", f"文件已不存在：\n{path}")
            return
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(path.resolve()))])
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)



class PastePacketWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(920, 720)
        self.setMinimumSize(760, 600)
        self.setAcceptDrops(True)

        self.build_ui()
        self.apply_style()
        self.apply_topmost()
        self.load_recent_files()
        self.statusBar().showMessage("准备就绪：可粘贴文本，也可拖入真实路径文件。")

    def load_settings(self) -> dict:
        default_settings = {
            "output_dir": str(DEFAULT_OUTPUT_DIR),
            "source": "manual_paste",
            "filename_mode": "random",
            "sequence_prefix": "LOG",
            "sequence_next": 1,
            "custom_filename": "LOG",
            "random_prefix": "LOG",
            "clear_after": True,
            "always_on_top": True,
            "split_enabled": False,
            "split_value": 500,
            "split_unit": "KB",
            # Empty means: use internal DEFAULT_TEMPLATE. Do not write the default
            # template into the UI; only show hints through placeholder text.
            "template": "",
        }
        data = dict(default_settings)
        if SETTINGS_PATH.exists():
            try:
                loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update(loaded)
            except Exception:
                pass

        # Migration: old v0.4.0 used WORK_DIR/log_packets as default. If a user
        # has not explicitly chosen another folder, move them to the stable
        # default directory. Custom output dirs are preserved.
        old_output = str(data.get("output_dir", "")).strip()
        try:
            if not old_output or Path(old_output).resolve() == LEGACY_OUTPUT_DIR.resolve():
                data["output_dir"] = str(DEFAULT_OUTPUT_DIR)
        except Exception:
            data["output_dir"] = str(DEFAULT_OUTPUT_DIR)

        # Migration: old builds stored DEFAULT_TEMPLATE in settings. New design
        # keeps the template editor empty and uses DEFAULT_TEMPLATE internally.
        if str(data.get("template", "")).strip() == DEFAULT_TEMPLATE.strip():
            data["template"] = ""

        mode = data.get("filename_mode", "random")
        if mode not in {"sequence", "custom", "random"}:
            data["filename_mode"] = "random"
        return data

    def save_settings(self):
        data = {
            "output_dir": self.output_dir_edit.text().strip() or str(DEFAULT_OUTPUT_DIR),
            "source": self.settings.get("source", "manual_paste"),
            "filename_mode": self.current_filename_mode(),
            "sequence_prefix": self.seq_prefix_edit.text().strip() or "LOG",
            "sequence_next": self.seq_spin.value(),
            "custom_filename": self.custom_name_edit.text().strip() or "LOG",
            "random_prefix": self.random_prefix_edit.text().strip() or "LOG",
            "clear_after": self.clear_after_check.isChecked(),
            "always_on_top": self.topmost_action.isChecked(),
            "split_enabled": self.split_check.isChecked(),
            "split_value": self.split_spin.value(),
            "split_unit": self.split_unit_combo.currentText(),
            "template": self.template_edit.toPlainText(),
        }
        SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(14, 12, 14, 10)
        main.setSpacing(8)

        # Top line: concise product explanation + pin button. The pin button
        # stays in the header and must not occupy a separate right-side block.
        top = QHBoxLayout()
        intro = QLabel(
            "粘贴文本 → 生成 TXT 日志包；拖入文件 → 复制改名并保存。"
            "两种输入互不污染，原文件不修改。"
        )
        intro.setObjectName("IntroLabel")
        intro.setWordWrap(True)
        top.addWidget(intro, 1)

        self.topmost_action = QAction("📌", self)
        self.topmost_action.setCheckable(True)
        self.topmost_action.setChecked(bool(self.settings.get("always_on_top", True)))
        self.topmost_action.setToolTip("窗口置顶")
        self.topmost_action.triggered.connect(self.apply_topmost)

        pin_button = QPushButton("📌")
        pin_button.setObjectName("PinButton")
        pin_button.setToolTip("窗口置顶 / 取消置顶")
        pin_button.setCheckable(True)
        pin_button.setChecked(self.topmost_action.isChecked())
        pin_button.clicked.connect(self.toggle_pin_button)
        self.pin_button = pin_button
        top.addWidget(pin_button)
        main.addLayout(top)

        # Main text area. It is the primary paste entrance and also supports
        # dropping real local files. The separate big file-drop panel was removed
        # in v0.4.2 to avoid duplicate visual entrances and squeezed settings.
        self.text_edit = DropTextEdit(self.import_files)
        self.text_edit.setObjectName("MainTextEdit")
        self.text_edit.setMinimumHeight(135)
        main.addWidget(self.text_edit, 2)

        # Main action row. File picking buttons are kept here after removing the
        # large file-drop panel; drag-to-text-area remains supported.
        row = QHBoxLayout()
        self.generate_btn = QPushButton("生成 TXT 文件")
        self.generate_btn.clicked.connect(self.generate_txt)
        row.addWidget(self.generate_btn)

        clear_btn = QPushButton("清空输入")
        clear_btn.clicked.connect(self.text_edit.clear)
        row.addWidget(clear_btn)

        choose_img = QPushButton("选择图片")
        choose_img.setToolTip("选择图片并复制改名到输出目录，保留扩展名，不修改原文件。")
        choose_img.clicked.connect(self.choose_images)
        row.addWidget(choose_img)

        choose_file = QPushButton("选择任意文件")
        choose_file.setToolTip("选择任意真实文件并复制改名到输出目录，保留扩展名，不修改原文件。")
        choose_file.clicked.connect(self.choose_any_files)
        row.addWidget(choose_file)

        open_btn = QPushButton("打开输出文件夹")
        open_btn.clicked.connect(self.open_output_folder)
        row.addWidget(open_btn)

        copy_btn = QPushButton("复制选中文件路径")
        copy_btn.clicked.connect(self.copy_selected_path)
        row.addWidget(copy_btn)

        self.clear_after_check = QCheckBox("生成后自动清空输入框")
        self.clear_after_check.setChecked(bool(self.settings.get("clear_after", True)))
        row.addWidget(self.clear_after_check)
        row.addStretch(1)
        main.addLayout(row)

        # Settings tabs. The filename tab must keep enough height so the output
        # directory and three mutually exclusive naming modes are fully visible.
        tabs = QTabWidget()
        tabs.setMinimumHeight(330)
        tabs.addTab(self.build_filename_tab(), "文件名")
        tabs.addTab(self.build_template_tab(), "模板")
        tabs.addTab(self.build_split_tab(), "超长拆分")
        main.addWidget(tabs, 3)

        # Recent files.
        recent_group = QGroupBox("最近生成/导入的文件")
        recent_layout = QVBoxLayout(recent_group)
        self.recent_list = DraggableRecentList()
        self.recent_list.setMinimumHeight(90)
        self.recent_list.itemDoubleClicked.connect(self.reveal_selected_file)
        recent_layout.addWidget(self.recent_list)
        main.addWidget(recent_group, 1)

    def build_filename_tab(self) -> QWidget:
        """Build the filename/settings tab.

        v0.4.6 keeps v0.4.5's three-card naming selector but compacts
        the small explanatory copy into each header row, so the section fits
        inside a normal-height window without clipping.
        """
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Output directory: compact header + one clear control row.
        output_group = QGroupBox("")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(12, 8, 12, 8)
        output_layout.setSpacing(6)

        output_header = QHBoxLayout()
        output_title = QLabel("输出目录")
        output_title.setObjectName("SectionTitle")
        output_header.addWidget(output_title)
        output_hint = QLabel("当前目录已通过写入测试；仍建议避免 Temp / Downloads / Desktop / OneDrive。")
        output_hint.setObjectName("HintLabel")
        output_hint.setWordWrap(False)
        output_header.addWidget(output_hint, 1)
        output_layout.addLayout(output_header)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("保存到"))
        self.output_dir_edit = QLineEdit(self.settings.get("output_dir", str(DEFAULT_OUTPUT_DIR)))
        self.output_dir_edit.setMinimumWidth(360)
        output_row.addWidget(self.output_dir_edit, 1)

        choose_dir = QPushButton("选择目录")
        choose_dir.setMinimumWidth(86)
        choose_dir.clicked.connect(self.choose_output_dir)
        output_row.addWidget(choose_dir)

        open_dir = QPushButton("打开目录")
        open_dir.setMinimumWidth(86)
        open_dir.clicked.connect(self.open_output_folder)
        output_row.addWidget(open_dir)
        output_layout.addLayout(output_row)
        layout.addWidget(output_group)

        # Naming mode: three obvious one-of-three cards, with no separate
        # explanatory paragraphs that waste vertical space.
        name_group = QGroupBox("")
        name_layout = QVBoxLayout(name_group)
        name_layout.setContentsMargins(14, 8, 14, 10)
        name_layout.setSpacing(8)

        name_header = QHBoxLayout()
        name_title = QLabel("命名方式（三选一）")
        name_title.setObjectName("SectionTitle")
        name_header.addWidget(name_title)

        name_hint = QLabel("三种模式互斥；当前选中会同时用于 TXT 生成和文件拖入改名。")
        name_hint.setObjectName("HintLabel")
        name_hint.setWordWrap(False)
        name_header.addWidget(name_hint, 1)

        self.current_mode_label = QLabel("")
        self.current_mode_label.setObjectName("CurrentModeLabel")
        self.current_mode_label.setWordWrap(False)
        self.current_mode_label.setMinimumWidth(330)
        name_header.addWidget(self.current_mode_label)
        name_layout.addLayout(name_header)

        self.mode_sequence = QRadioButton("递增序号")
        self.mode_custom = QRadioButton("自定义名称")
        self.mode_random = QRadioButton("随机短码")
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.mode_sequence)
        self.mode_group.addButton(self.mode_custom)
        self.mode_group.addButton(self.mode_random)

        mode = self.settings.get("filename_mode", "random")
        self.mode_sequence.setChecked(mode == "sequence")
        self.mode_custom.setChecked(mode == "custom")
        self.mode_random.setChecked(mode == "random")
        if not any([self.mode_sequence.isChecked(), self.mode_custom.isChecked(), self.mode_random.isChecked()]):
            self.mode_random.setChecked(True)

        self.seq_prefix_edit = QLineEdit(self.settings.get("sequence_prefix", "LOG"))
        self.seq_prefix_edit.setMaximumWidth(120)
        self.seq_spin = QSpinBox()
        self.seq_spin.setRange(1, 999999)
        self.seq_spin.setValue(int(self.settings.get("sequence_next", 1)))
        self.seq_spin.setMaximumWidth(105)

        self.custom_name_edit = QLineEdit(self.settings.get("custom_filename", "LOG"))
        self.custom_name_edit.setPlaceholderText("例如：Unity_Build_Error")

        self.random_prefix_edit = QLineEdit(self.settings.get("random_prefix", "LOG"))
        self.random_prefix_edit.setMaximumWidth(150)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self.mode_cards = {}

        def make_mode_card(mode_key: str, radio: QRadioButton, controls: QHBoxLayout, header_note: str) -> QFrame:
            card = QFrame()
            card.setObjectName("ModeCard")
            card.setMinimumHeight(96)
            card.setProperty("selectedMode", False)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            card_layout.setSpacing(6)

            title_row = QHBoxLayout()
            radio.setMinimumHeight(26)
            radio.setCursor(Qt.PointingHandCursor)
            title_row.addWidget(radio)
            note = QLabel(header_note)
            note.setObjectName("HintLabel")
            note.setWordWrap(False)
            title_row.addWidget(note, 1)
            card_layout.addLayout(title_row)

            card_layout.addLayout(controls)
            card_layout.addStretch(1)

            def select_this(event, r=radio):
                r.setChecked(True)
                self.update_mode_cards()
                event.accept()
            card.mousePressEvent = select_this  # type: ignore[method-assign]

            self.mode_cards[mode_key] = card
            return card

        seq_controls = QHBoxLayout()
        seq_controls.addWidget(QLabel("前缀"))
        seq_controls.addWidget(self.seq_prefix_edit)
        seq_controls.addWidget(QLabel("下一个序号"))
        seq_controls.addWidget(self.seq_spin)
        seq_controls.addStretch(1)
        cards_row.addWidget(make_mode_card(
            "sequence",
            self.mode_sequence,
            seq_controls,
            "连续整理｜例 LOG_001.txt、LOG_002.png",
        ), 1)

        custom_controls = QHBoxLayout()
        custom_controls.addWidget(QLabel("文件名"))
        custom_controls.addWidget(self.custom_name_edit, 1)
        cards_row.addWidget(make_mode_card(
            "custom",
            self.mode_custom,
            custom_controls,
            "明确命名｜重名自动加 _2",
        ), 1)

        random_controls = QHBoxLayout()
        random_controls.addWidget(QLabel("前缀"))
        random_controls.addWidget(self.random_prefix_edit)
        random_controls.addStretch(1)
        cards_row.addWidget(make_mode_card(
            "random",
            self.mode_random,
            random_controls,
            "高频临时包｜推荐默认使用",
        ), 1)

        name_layout.addLayout(cards_row)
        layout.addWidget(name_group)
        layout.addStretch(1)

        for radio in (self.mode_sequence, self.mode_custom, self.mode_random):
            radio.toggled.connect(self.update_mode_cards)
        for widget in (self.seq_prefix_edit, self.custom_name_edit, self.random_prefix_edit):
            widget.textChanged.connect(self.update_mode_cards)
        self.seq_spin.valueChanged.connect(self.update_mode_cards)
        self.update_mode_cards()
        return w

    def update_mode_cards(self):
        """Refresh selected-card styling and the current mode summary."""
        if not hasattr(self, "mode_cards"):
            return
        mode = self.current_filename_mode()
        labels = {
            "sequence": f"当前：递增序号｜下一个：{sanitize_stem(self.seq_prefix_edit.text(), 'LOG')}_{self.seq_spin.value():03d}.txt",
            "custom": f"当前：自定义名称｜示例：{sanitize_stem(self.custom_name_edit.text(), 'LOG')}.txt",
            "random": f"当前：随机短码｜示例：{sanitize_stem(self.random_prefix_edit.text(), 'LOG')}_483927.txt",
        }
        if hasattr(self, "current_mode_label"):
            self.current_mode_label.setText(labels.get(mode, "当前命名方式：未选择"))
        for key, card in self.mode_cards.items():
            card.setProperty("selectedMode", key == mode)
            card.style().unpolish(card)
            card.style().polish(card)

    def build_template_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        help_label = QLabel(
            "模板框默认留空：留空时使用内置默认模板。提示文字只是占位说明，不会写入模板。"
            "如需自定义模板，必须包含 {raw_content}。"
        )
        help_label.setObjectName("HintLabel")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        self.template_edit = QTextEdit()
        self.template_edit.setPlaceholderText(
            "这里可以自定义 TXT 模板。\n\n"
            "可用占位符：\n"
            "{packet_id}   文件名主干\n"
            "{created_at}  生成时间\n"
            "{source}      来源标记\n"
            "{file_name}   完整文件名\n"
            "{part_index}  当前拆分片序号\n"
            "{part_total}  拆分总片数\n"
            "{raw_content} 原始日志内容\n\n"
            "模板必须包含 {raw_content}。\n"
            "如果这里保持为空，程序使用内置默认模板生成 TXT。"
        )
        self.template_edit.setPlainText(self.settings.get("template", ""))
        layout.addWidget(self.template_edit)
        reset_btn = QPushButton("清空自定义模板（使用内置默认模板）")
        reset_btn.clicked.connect(lambda: self.template_edit.setPlainText(""))
        layout.addWidget(reset_btn)
        return w

    def build_split_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        self.split_check = QCheckBox("超长文本拆分为多个 TXT")
        self.split_check.setChecked(bool(self.settings.get("split_enabled", False)))
        self.split_spin = QSpinBox()
        self.split_spin.setRange(1, 999999)
        self.split_spin.setValue(int(self.settings.get("split_value", 500)))
        self.split_unit_combo = QComboBox()
        self.split_unit_combo.addItems(["B", "KB", "MB"])
        self.split_unit_combo.setCurrentText(self.settings.get("split_unit", "KB"))
        layout.addWidget(self.split_check)
        layout.addWidget(QLabel("单片上限"))
        layout.addWidget(self.split_spin)
        layout.addWidget(self.split_unit_combo)
        layout.addStretch(1)
        return w

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #F7F8FA;
                color: #1F2328;
                font-family: "Segoe UI", "Microsoft YaHei UI";
                font-size: 9.5pt;
            }
            QLabel#IntroLabel {
                color: #30363D;
            }
            QLabel#HintLabel {
                color: #6B7280;
                font-size: 9pt;
            }
            QLabel#SectionTitle {
                color: #111827;
                font-weight: 700;
                font-size: 10.5pt;
            }
            QPlainTextEdit#MainTextEdit {
                background: #FFFFFF;
                border: 1px solid #D0D7DE;
                border-radius: 10px;
                padding: 8px;
                font-family: Consolas, "Microsoft YaHei UI";
                font-size: 10pt;
            }
            QPlainTextEdit#MainTextEdit[dragActive="true"] {
                border: 2px solid #3B82F6;
                background: #EFF6FF;
            }

            QFrame#ModeCard {
                background: #FFFFFF;
                border: 1px solid #D0D7DE;
                border-radius: 10px;
            }
            QFrame#ModeCard[selectedMode="true"] {
                background: #EEF6FF;
                border: 2px solid #2563EB;
            }
            QFrame#ModeCard:hover {
                border-color: #7CA8E8;
                background: #F8FBFF;
            }
            QLabel#CurrentModeLabel {
                background: #EEF6FF;
                color: #1E3A8A;
                border: 1px solid #BFDBFE;
                border-radius: 8px;
                padding: 4px 8px;
                font-weight: 600;
            }
            QRadioButton {
                font-weight: 700;
                font-size: 10.5pt;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QFrame#DropPanel {
                background: #FFFFFF;
                border: 1px dashed #9CA3AF;
                border-radius: 12px;
            }
            QFrame#DropPanel[dragActive="true"] {
                background: #EFF6FF;
                border: 2px solid #3B82F6;
            }
            QLabel#DropPanelTitle {
                font-weight: 600;
                color: #111827;
            }
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #D0D7DE;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background: #F3F4F6;
                border-color: #9CA3AF;
            }
            QPushButton:pressed {
                background: #E5E7EB;
            }
            QPushButton#PinButton {
                min-width: 34px;
                max-width: 34px;
                font-size: 13pt;
            }
            QGroupBox {
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QTabWidget::pane {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background: #FFFFFF;
            }
            QTabBar::tab {
                padding: 7px 12px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-bottom: none;
            }
            QLineEdit, QTextEdit, QListWidget, QSpinBox, QComboBox {
                background: #FFFFFF;
                border: 1px solid #D0D7DE;
                border-radius: 7px;
                padding: 4px;
            }
        """)

    def apply_topmost(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.topmost_action.isChecked())
        self.show()
        if hasattr(self, "pin_button"):
            self.pin_button.setChecked(self.topmost_action.isChecked())
            self.pin_button.setText("📌" if self.topmost_action.isChecked() else "📍")
        self.save_settings_safe()

    def toggle_pin_button(self, checked: bool):
        self.topmost_action.setChecked(checked)
        self.apply_topmost()

    def current_filename_mode(self) -> str:
        if self.mode_custom.isChecked():
            return "custom"
        if self.mode_random.isChecked():
            return "random"
        return "sequence"

    def output_dir(self) -> Path:
        folder = Path(self.output_dir_edit.text().strip() or str(DEFAULT_OUTPUT_DIR)).expanduser()
        return ensure_stable_output_dir(folder)

    def next_stem(self, suffix: str = ".txt") -> str:
        mode = self.current_filename_mode()
        if mode == "custom":
            return sanitize_stem(self.custom_name_edit.text(), "LOG")
        if mode == "random":
            prefix = sanitize_stem(self.random_prefix_edit.text(), "LOG")
            folder = self.output_dir()
            for _ in range(50):
                stem = f"{prefix}_{random.randint(100000, 999999)}"
                if not (folder / f"{stem}{suffix}").exists():
                    return stem
            return f"{prefix}_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"
        prefix = sanitize_stem(self.seq_prefix_edit.text(), "LOG")
        return f"{prefix}_{self.seq_spin.value():03d}"

    def advance_sequence_if_needed(self):
        if self.current_filename_mode() == "sequence":
            self.seq_spin.setValue(self.seq_spin.value() + 1)

    def split_limit_bytes(self) -> int:
        value = self.split_spin.value()
        unit = self.split_unit_combo.currentText()
        if unit == "KB":
            return value * 1024
        if unit == "MB":
            return value * 1024 * 1024
        return value

    def generate_txt(self):
        raw = self.text_edit.toPlainText()
        if not raw.strip():
            QMessageBox.information(self, "提示", "输入为空，无法生成。")
            return
        template = self.template_edit.toPlainText()
        if not template.strip():
            template = DEFAULT_TEMPLATE
        elif "{raw_content}" not in template:
            QMessageBox.warning(self, "模板错误", "模板必须包含 {raw_content}。")
            return

        chunks = [raw]
        if self.split_check.isChecked():
            chunks = split_by_bytes(raw, self.split_limit_bytes())

        folder = self.output_dir()
        base = self.next_stem(".txt")
        generated: List[Path] = []

        try:
            for idx, chunk in enumerate(chunks, start=1):
                stem = base if len(chunks) == 1 else f"{base}_part{idx:02d}"
                path = unique_path(folder, stem, ".txt")
                payload = template.format(
                    packet_id=path.stem,
                    created_at=now_text(),
                    source=self.settings.get("source", "manual_paste"),
                    file_name=path.name,
                    part_index=idx,
                    part_total=len(chunks),
                    raw_content=chunk,
                )
                safe_write_text(path, payload)
                generated.append(path)

            self.advance_sequence_if_needed()
            if self.clear_after_check.isChecked():
                self.text_edit.clear()
            self.save_settings()
            self.load_recent_files()
            self.statusBar().showMessage(f"已生成 {len(generated)} 个 TXT：{generated[0].name}")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "生成失败",
                f"生成失败：{exc}\n\n建议：把输出目录改到 D:\\GPT_LogPackets 或用户目录下的稳定文件夹，避免 Temp / Downloads / Desktop / OneDrive。"
            )

    def import_files(self, files: List[Path]):
        normal_files = [p for p in files if p.is_file()]
        if not normal_files:
            self.statusBar().showMessage("未发现可处理的普通文件；文件夹已跳过。")
            return

        folder = self.output_dir()
        copied: List[Path] = []
        try:
            for src in normal_files:
                suffix = src.suffix or ".bin"
                stem = self.next_stem(suffix)
                dst = unique_path(folder, stem, suffix)
                safe_copy_file(src, dst)
                copied.append(dst)
                self.advance_sequence_if_needed()

            self.save_settings()
            self.load_recent_files()
            self.statusBar().showMessage(f"已复制并重命名 {len(copied)} 个文件。")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "文件导入失败",
                f"文件导入失败：{exc}\n\n建议：把输出目录改到 D:\\GPT_LogPackets 或用户目录下的稳定文件夹，避免 Temp / Downloads / Desktop / OneDrive。"
            )

    def choose_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.webp *.gif *.bmp *.tif *.tiff *.heic *.heif);;All Files (*.*)",
        )
        self.import_files([Path(f) for f in files])

    def choose_any_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择任意文件", str(Path.home()), "All Files (*.*)")
        self.import_files([Path(f) for f in files])

    def choose_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_dir_edit.text())
        if folder:
            self.output_dir_edit.setText(folder)
            self.load_recent_files()

    def open_output_folder(self):
        folder = self.output_dir()
        if sys.platform.startswith("win"):
            os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def load_recent_files(self):
        self.recent_list.clear()
        folder = self.output_dir()
        if hasattr(self, "output_hint"):
            if is_risky_output_dir(folder):
                self.output_hint.setText("⚠ 当前目录可能受临时清理、桌面/下载目录清理或云同步影响；建议改到 D:\\GPT_LogPackets。")
            else:
                self.output_hint.setText("当前输出目录已通过写入测试。仍建议避免 Temp / Downloads / Desktop / OneDrive。")
        files = sorted([p for p in folder.iterdir() if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_RECENT]
        for p in files:
            size_kb = max(1, p.stat().st_size // 1024)
            item = QListWidgetItem(f"{p.name} | {size_kb} KB | {p.parent}")
            item.setData(Qt.UserRole, str(p))
            self.recent_list.addItem(item)

    def selected_recent_path(self) -> Optional[Path]:
        item = self.recent_list.currentItem()
        if not item:
            return None
        return Path(item.data(Qt.UserRole))

    def copy_selected_path(self):
        path = self.selected_recent_path()
        if not path:
            self.statusBar().showMessage("请先在最近文件列表中选择一个文件。")
            return
        QApplication.clipboard().setText(str(path))
        self.statusBar().showMessage(f"已复制路径：{path}")

    def reveal_selected_file(self):
        path = self.selected_recent_path()
        if not path:
            return
        if sys.platform.startswith("win"):
            os.system(f'explorer /select,"{path}"')
        else:
            self.open_output_folder()

    def save_settings_safe(self):
        try:
            if hasattr(self, "output_dir_edit"):
                self.save_settings()
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            self.save_settings()
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Segoe UI", 9))
    win = PastePacketWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        crash_path = WORK_DIR / "pastepacket_qt_crash.log"
        crash_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise
