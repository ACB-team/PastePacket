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
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QAction
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
APP_VERSION = "0.4.0"
WORK_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = WORK_DIR / "pastepacket_qt_settings.json"
DEFAULT_OUTPUT_DIR = WORK_DIR / "log_packets"
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


class DropTextEdit(QPlainTextEdit):
    def __init__(self, on_files_dropped, parent=None):
        super().__init__(parent)
        self.on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)
        self.setPlaceholderText("粘贴长日志生成 TXT；也可把真实文件路径的图片/日志/文档/任意普通文件拖到这里自动复制改名。")

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
        self.title = QLabel("拖入文件到这里：微信图片 / 截图 / 日志 / 代码 / 文档 / 任意普通文件")
        self.title.setObjectName("DropPanelTitle")
        self.hint = QLabel("仅支持真实文件路径；拖入后复制到输出目录并按当前命名规则重命名，保留扩展名，原文件不修改。")
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
        if SETTINGS_PATH.exists():
            try:
                return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "output_dir": str(DEFAULT_OUTPUT_DIR),
            "source": "manual_paste",
            "filename_mode": "sequence",
            "sequence_prefix": "LOG",
            "sequence_next": 1,
            "custom_filename": "LOG",
            "random_prefix": "LOG",
            "clear_after": True,
            "always_on_top": True,
            "split_enabled": False,
            "split_value": 500,
            "split_unit": "KB",
            "template": DEFAULT_TEMPLATE,
        }

    def save_settings(self):
        data = {
            "output_dir": self.output_dir_edit.text().strip() or str(DEFAULT_OUTPUT_DIR),
            "source": self.source_edit.text().strip() or "manual_paste",
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
        main.setSpacing(10)

        # toolbar-like top line
        top = QHBoxLayout()
        intro = QLabel("可粘贴 Unity Console / 长日志 / Agent 回报生成 TXT；也可拖入真实文件路径的图片、日志、文档等任意普通文件，自动复制并重命名。")
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

        # Text area
        self.text_edit = DropTextEdit(self.import_files)
        self.text_edit.setObjectName("MainTextEdit")
        main.addWidget(self.text_edit, 3)

        # Action row
        row = QHBoxLayout()
        self.generate_btn = QPushButton("生成 TXT 文件")
        self.generate_btn.clicked.connect(self.generate_txt)
        row.addWidget(self.generate_btn)

        clear_btn = QPushButton("清空输入")
        clear_btn.clicked.connect(self.text_edit.clear)
        row.addWidget(clear_btn)

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

        # Drag/file panel
        file_group = QGroupBox("文件/图片拖入改名")
        file_layout = QGridLayout(file_group)
        file_layout.setContentsMargins(10, 10, 10, 10)
        self.drop_panel = DropPanel(self.import_files)
        file_layout.addWidget(self.drop_panel, 0, 0, 2, 1)

        choose_img = QPushButton("选择图片")
        choose_img.clicked.connect(self.choose_images)
        choose_file = QPushButton("选择任意文件")
        choose_file.clicked.connect(self.choose_any_files)
        file_layout.addWidget(choose_img, 0, 1)
        file_layout.addWidget(choose_file, 0, 2)

        file_hint = QLabel("说明：拖入和选择文件都只做复制改名，不读取内容、不联网、不修改原文件。文件夹会被跳过。")
        file_hint.setObjectName("HintLabel")
        file_hint.setWordWrap(True)
        file_layout.addWidget(file_hint, 1, 1, 1, 2)
        file_layout.setColumnStretch(0, 1)
        main.addWidget(file_group)

        # Settings tabs
        tabs = QTabWidget()
        tabs.addTab(self.build_filename_tab(), "文件名")
        tabs.addTab(self.build_template_tab(), "模板")
        tabs.addTab(self.build_split_tab(), "超长拆分")
        main.addWidget(tabs, 2)

        # Recent
        recent_group = QGroupBox("最近生成/导入的文件")
        recent_layout = QVBoxLayout(recent_group)
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self.reveal_selected_file)
        recent_layout.addWidget(self.recent_list)
        main.addWidget(recent_group, 1)

    def build_filename_tab(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)

        self.output_dir_edit = QLineEdit(self.settings.get("output_dir", str(DEFAULT_OUTPUT_DIR)))
        choose_dir = QPushButton("选择目录")
        choose_dir.clicked.connect(self.choose_output_dir)
        grid.addWidget(QLabel("输出目录"), 0, 0)
        grid.addWidget(self.output_dir_edit, 0, 1, 1, 4)
        grid.addWidget(choose_dir, 0, 5)

        self.source_edit = QLineEdit(self.settings.get("source", "manual_paste"))
        grid.addWidget(QLabel("来源标记"), 1, 0)
        grid.addWidget(self.source_edit, 1, 1)

        self.mode_sequence = QRadioButton("规则文件名：前缀 + 递增序号")
        self.mode_custom = QRadioButton("自定义文件名")
        self.mode_random = QRadioButton("随机码文件名")

        mode = self.settings.get("filename_mode", "sequence")
        self.mode_sequence.setChecked(mode == "sequence")
        self.mode_custom.setChecked(mode == "custom")
        self.mode_random.setChecked(mode == "random")

        self.seq_prefix_edit = QLineEdit(self.settings.get("sequence_prefix", "LOG"))
        self.seq_spin = QSpinBox()
        self.seq_spin.setRange(1, 999999)
        self.seq_spin.setValue(int(self.settings.get("sequence_next", 1)))

        self.custom_name_edit = QLineEdit(self.settings.get("custom_filename", "LOG"))
        self.random_prefix_edit = QLineEdit(self.settings.get("random_prefix", "LOG"))

        grid.addWidget(self.mode_sequence, 2, 0, 1, 2)
        grid.addWidget(QLabel("前缀"), 2, 2)
        grid.addWidget(self.seq_prefix_edit, 2, 3)
        grid.addWidget(QLabel("下一个序号"), 2, 4)
        grid.addWidget(self.seq_spin, 2, 5)

        grid.addWidget(self.mode_custom, 3, 0, 1, 2)
        grid.addWidget(QLabel("文件名"), 3, 2)
        grid.addWidget(self.custom_name_edit, 3, 3, 1, 3)

        grid.addWidget(self.mode_random, 4, 0, 1, 2)
        grid.addWidget(QLabel("前缀"), 4, 2)
        grid.addWidget(self.random_prefix_edit, 4, 3)

        grid.setColumnStretch(3, 1)
        return w

    def build_template_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        help_label = QLabel("可用占位符：{packet_id}、{created_at}、{source}、{file_name}、{part_index}、{part_total}、{raw_content}。必须包含 {raw_content}。")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        self.template_edit = QTextEdit()
        self.template_edit.setPlainText(self.settings.get("template", DEFAULT_TEMPLATE))
        layout.addWidget(self.template_edit)
        reset_btn = QPushButton("恢复默认模板")
        reset_btn.clicked.connect(lambda: self.template_edit.setPlainText(DEFAULT_TEMPLATE))
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
        folder.mkdir(parents=True, exist_ok=True)
        return folder

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
        if "{raw_content}" not in template:
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
                    source=self.source_edit.text().strip() or "manual_paste",
                    file_name=path.name,
                    part_index=idx,
                    part_total=len(chunks),
                    raw_content=chunk,
                )
                path.write_text(payload, encoding="utf-8")
                generated.append(path)

            self.advance_sequence_if_needed()
            if self.clear_after_check.isChecked():
                self.text_edit.clear()
            self.save_settings()
            self.load_recent_files()
            self.statusBar().showMessage(f"已生成 {len(generated)} 个 TXT：{generated[0].name}")
        except Exception as exc:
            QMessageBox.critical(self, "生成失败", str(exc))

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
                shutil.copy2(src, dst)
                copied.append(dst)
                self.advance_sequence_if_needed()

            self.save_settings()
            self.load_recent_files()
            self.statusBar().showMessage(f"已复制并重命名 {len(copied)} 个文件。")
        except Exception as exc:
            QMessageBox.critical(self, "文件导入失败", str(exc))

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
