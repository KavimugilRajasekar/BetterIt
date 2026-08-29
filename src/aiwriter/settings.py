"""Settings and Tag Manager window for BetterIt.

Follows BetterIt's signature aesthetic: frameless window with translucent mint/green
backdrop, 3px dark border, fully rounded corners, draggable custom header bar,
spacious cards, and rounded interactive controls.
"""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBitmap,
    QBrush,
    QColor,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QRegion,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from .tag_store import DEFAULT_TAGS, TagStore
    from .theme import STYLESHEET
except ImportError:
    from tag_store import DEFAULT_TAGS, TagStore
    from theme import STYLESHEET

WINDOW_WIDTH = 750
WINDOW_HEIGHT = 520
CORNER_RADIUS = 28


# --- "Edit Tag" page ----------------------------------------------------

class EditTagPage(QWidget):
    """List existing tags on the left; edit the selected one's name/prompt
    on the right. Supports adding, editing, and deleting tags."""

    tags_changed = Signal()

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store
        self._current_name: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # -- Left Card: tag list + New button --
        left_card = QFrame()
        left_card.setObjectName("SettingsCard")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(10)

        left_label = QLabel("Your Tags")
        left_label.setObjectName("SectionLabel")
        left_layout.addWidget(left_label)

        self._list = QListWidget()
        self._list.setObjectName("TagList")
        self._list.setFixedWidth(190)
        left_layout.addWidget(self._list, 1)

        new_btn = QPushButton("+ New Tag")
        new_btn.setObjectName("Secondary")
        new_btn.setFixedHeight(38)
        new_btn.clicked.connect(self._on_new)
        left_layout.addWidget(new_btn)

        layout.addWidget(left_card)

        # -- Right Card: Edit Form --
        right_card = QFrame()
        right_card.setObjectName("SettingsCard")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        name_label = QLabel("Tag Name")
        name_label.setObjectName("SectionLabel")
        right_layout.addWidget(name_label)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. LinkedIn Post, Professional Email, etc.")
        right_layout.addWidget(self._name_edit)

        # Prompt Header with Raw vs Markdown View switcher
        prompt_header = QHBoxLayout()
        prompt_header.setSpacing(8)

        prompt_label = QLabel("Rewrite Prompt / Instructions")
        prompt_label.setObjectName("SectionLabel")
        prompt_header.addWidget(prompt_label)
        prompt_header.addStretch(1)

        self._raw_view_btn = QPushButton("Raw")
        self._raw_view_btn.setObjectName("ViewToggle")
        self._raw_view_btn.setCheckable(True)
        self._raw_view_btn.setChecked(True)
        self._raw_view_btn.clicked.connect(self._show_raw_view)
        prompt_header.addWidget(self._raw_view_btn)

        self._md_view_btn = QPushButton("Markdown")
        self._md_view_btn.setObjectName("ViewToggle")
        self._md_view_btn.setCheckable(True)
        self._md_view_btn.setChecked(False)
        self._md_view_btn.clicked.connect(self._show_md_view)
        prompt_header.addWidget(self._md_view_btn)

        right_layout.addLayout(prompt_header)

        sub_label = QLabel("Define how selected text should be transformed when this tag is chosen:")
        sub_label.setObjectName("SubLabel")
        sub_label.setWordWrap(True)
        right_layout.addWidget(sub_label)

        # Stacked Prompt Editor: Raw Edit (0) and Markdown Rendered View (1)
        self._prompt_stack = QStackedWidget()

        self._prompt_edit = QTextEdit()
        self._prompt_edit.setPlaceholderText(
            "Describe the desired style, audience, tone, and formatting for this tag... (Markdown supported)"
        )
        self._prompt_edit.textChanged.connect(self._sync_preview_text)
        self._prompt_stack.addWidget(self._prompt_edit)

        self._prompt_preview = QTextEdit()
        self._prompt_preview.setReadOnly(True)
        self._prompt_preview.setPlaceholderText("Markdown preview will appear here...")
        self._prompt_stack.addWidget(self._prompt_preview)

        right_layout.addWidget(self._prompt_stack, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setObjectName("Danger")
        self._delete_btn.setFixedHeight(38)
        self._delete_btn.setMinimumWidth(90)
        self._delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self._delete_btn)

        btn_row.addStretch(1)

        self._save_btn = QPushButton("Save Tag")
        self._save_btn.setObjectName("Primary")
        self._save_btn.setFixedHeight(38)
        self._save_btn.setMinimumWidth(110)
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)

        right_layout.addLayout(btn_row)
        layout.addWidget(right_card, 1)

        self._list.currentTextChanged.connect(self._on_list_selection)
        self.reload()

    def _show_raw_view(self) -> None:
        self._raw_view_btn.setChecked(True)
        self._md_view_btn.setChecked(False)
        self._prompt_stack.setCurrentIndex(0)

    def _show_md_view(self) -> None:
        self._raw_view_btn.setChecked(False)
        self._md_view_btn.setChecked(True)
        self._sync_preview_text()
        self._prompt_stack.setCurrentIndex(1)

    def _sync_preview_text(self) -> None:
        raw_text = self._prompt_edit.toPlainText()
        self._prompt_preview.setMarkdown(raw_text)

    def reload(self, select: str | None = None) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        names = self._store.names()
        for name in names:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            self._list.addItem(item)
        self._list.blockSignals(False)

        target = select if (select and select in names) else (names[0] if names else None)
        if target:
            for i in range(self._list.count()):
                item = self._list.item(i)
                if item.data(Qt.UserRole) == target:
                    self._list.setCurrentItem(item)
                    self._on_list_selection(target)
                    break
        else:
            self._on_new()

    def _on_list_selection(self, item_text: str) -> None:
        current_item = self._list.currentItem()
        if not current_item:
            return
        name = current_item.data(Qt.UserRole)
        if not name:
            return
        self._current_name = name
        self._name_edit.setText(name)
        prompt_content = self._store.prompt_for(name)
        self._prompt_edit.setPlainText(prompt_content)
        self._prompt_preview.setMarkdown(prompt_content)
        self._delete_btn.setEnabled(True)

    def _on_new(self) -> None:
        self._list.clearSelection()
        self._list.setCurrentRow(-1)
        self._current_name = None
        self._name_edit.clear()
        self._prompt_edit.clear()
        self._prompt_preview.clear()
        self._show_raw_view()
        self._delete_btn.setEnabled(False)
        self._name_edit.setFocus()

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        prompt = self._prompt_edit.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please give this tag a name.")
            return
        if not prompt:
            QMessageBox.warning(self, "Missing Prompt", "Please write transformation instructions for this tag.")
            return

        clashes = any(
            existing.lower() == name.lower() and existing != self._current_name
            for existing in self._store.names()
        )
        if clashes:
            QMessageBox.warning(self, "Duplicate Tag", f'A tag named "{name}" already exists.')
            return

        if self._current_name and self._current_name != name:
            self._store.rename(self._current_name, name, prompt)
        else:
            self._store.set_tag(name, prompt)

        self.reload(select=name)
        self.tags_changed.emit()

    def _on_delete(self) -> None:
        if not self._current_name:
            return
        confirm = QMessageBox.question(
            self,
            "Delete Tag",
            f'Are you sure you want to delete the tag "{self._current_name}"?',
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        if self._store.delete(self._current_name):
            self._current_name = None
            self.reload()
            self.tags_changed.emit()
        else:
            QMessageBox.information(
                self, "Cannot Delete", "At least one tag must remain in BetterIt."
            )


# --- "General" page ------------------------------------------------------

class GeneralSettingsPage(QWidget):
    """App-wide settings: default tag, hotkey info, reset tags."""

    tags_changed = Signal()

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("SettingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(16)

        # Title
        sec_title = QLabel("General Preferences")
        sec_title.setObjectName("SectionLabel")
        card_layout.addWidget(sec_title)

        # Default tag row
        default_row = QHBoxLayout()
        default_row.setSpacing(12)
        default_lbl = QLabel("Default tag on window open:")
        default_lbl.setObjectName("SubLabel")
        default_row.addWidget(default_lbl)

        self._default_combo = QComboBox()
        self._default_combo.setMinimumWidth(180)
        self._default_combo.currentTextChanged.connect(self._on_default_tag_changed)
        default_row.addWidget(self._default_combo, 1)
        card_layout.addLayout(default_row)

        # Always on top
        self._always_on_top = QCheckBox("Keep the floating window always on top")
        saved_on_top = self._store.get_config("always_on_top", True)
        self._always_on_top.setChecked(bool(saved_on_top))
        self._always_on_top.toggled.connect(self._on_always_on_top_toggled)
        card_layout.addWidget(self._always_on_top)

        # Hotkey Info card
        hotkey_card = QFrame()
        hotkey_card.setObjectName("InnerCard")
        hotkey_layout = QVBoxLayout(hotkey_card)
        hotkey_layout.setContentsMargins(12, 10, 12, 10)
        hotkey_layout.setSpacing(4)

        hotkey_title = QLabel("Global Trigger Shortcut")
        hotkey_title.setObjectName("SectionLabel")
        hotkey_layout.addWidget(hotkey_title)

        hotkey_val = os.environ.get("HOTKEY", "Ctrl + Space")
        hotkey_desc = QLabel(
            f"Select any text in any application and press  <b>{hotkey_val}</b>  to open BetterIt."
        )
        hotkey_desc.setObjectName("SubLabel")
        hotkey_layout.addWidget(hotkey_desc)
        card_layout.addWidget(hotkey_card)

        card_layout.addStretch(1)

        # Reset button
        reset_row = QHBoxLayout()
        reset_row.addStretch(1)
        reset_btn = QPushButton("Reset All Tags to Defaults")
        reset_btn.setObjectName("Secondary")
        reset_btn.setFixedHeight(36)
        reset_btn.clicked.connect(self._on_reset)
        reset_row.addWidget(reset_btn)
        card_layout.addLayout(reset_row)

        layout.addWidget(card)
        self.refresh()

    def refresh(self) -> None:
        current_saved = self._store.get_config("default_tag", "Grammar & Clarity")
        self._default_combo.blockSignals(True)
        self._default_combo.clear()
        names = self._store.names()
        self._default_combo.addItems(names)
        if current_saved in names:
            self._default_combo.setCurrentText(current_saved)
        elif names:
            self._default_combo.setCurrentIndex(0)
        self._default_combo.blockSignals(False)

    def _on_default_tag_changed(self, text: str) -> None:
        if text:
            self._store.set_config("default_tag", text)

    def _on_always_on_top_toggled(self, checked: bool) -> None:
        self._store.set_config("always_on_top", checked)

    def _on_reset(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Reset Tags",
            "This will restore all built-in tags to their initial defaults. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        self._store.reset_to_defaults()
        self.refresh()
        self.tags_changed.emit()


# --- "AI Model" page -----------------------------------------------------

class AIModelPage(QWidget):
    """Configuration for OpenRouter model and AI behavior."""

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("SettingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)

        sec_title = QLabel("AI Model Configuration")
        sec_title.setObjectName("SectionLabel")
        card_layout.addWidget(sec_title)

        model_desc = QLabel("Select or enter the OpenRouter model used for text transformations:")
        model_desc.setObjectName("SubLabel")
        card_layout.addWidget(model_desc)

        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        models = [
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-haiku",
            "google/gemini-2.5-flash",
            "deepseek/deepseek-chat",
            "meta-llama/llama-3.3-70b-instruct",
        ]
        self._model_combo.addItems(models)

        saved_model = self._store.get_config("model") or os.environ.get("MODEL", "openai/gpt-4o-mini")
        if saved_model:
            self._model_combo.setCurrentText(saved_model)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        card_layout.addWidget(self._model_combo)

        # API info card
        api_card = QFrame()
        api_card.setObjectName("InnerCard")
        api_layout = QVBoxLayout(api_card)
        api_layout.setContentsMargins(12, 10, 12, 10)
        api_layout.setSpacing(4)

        api_title = QLabel("API Key Status")
        api_title.setObjectName("SectionLabel")
        api_layout.addWidget(api_title)

        api_key = os.environ.get("OPEN_ROUTER", "")
        if api_key:
            masked = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 12 else "Configured"
            api_status = f"OpenRouter API Key configured: <b>{masked}</b>"
        else:
            api_status = "OPEN_ROUTER is not set. Add your OpenRouter API key to <code>.env</code>."

        api_desc = QLabel(api_status)
        api_desc.setObjectName("SubLabel")
        api_desc.setWordWrap(True)
        api_layout.addWidget(api_desc)
        card_layout.addWidget(api_card)

        card_layout.addStretch(1)
        layout.addWidget(card)

    def _on_model_changed(self, text: str) -> None:
        if text.strip():
            self._store.set_config("model", text.strip())
            os.environ["MODEL"] = text.strip()


# --- Settings Window -----------------------------------------------------

class SettingsWindow(QDialog):
    """
    Frameless, rounded dialog matching BetterIt's signature look & feel.
    Features drag support, custom close button, sidebar navigation, and cards.
    """

    tags_changed = Signal()

    PAGES = [
        ("Edit Tags", "Edit Tag"),
        ("General", "General"),
        ("AI Model", "AI Model"),
    ]

    def __init__(
        self,
        tag_store: TagStore,
        parent: QWidget | None = None,
        initial_page: str = "Edit Tag",
    ) -> None:
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("SettingsDialog")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(QSize(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.setMask(self._rounded_mask(WINDOW_WIDTH, WINDOW_HEIGHT, CORNER_RADIUS))

        self._tag_store = tag_store
        self._drag_pos: QPoint | None = None

        # Main background container
        self._container = QWidget(self)
        self._container.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self._container.setObjectName("SettingsWindow")
        self._container.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._wire_signals()

        # Drag support on container
        self._container.mousePressEvent = self._mouse_press_event
        self._container.mouseMoveEvent = self._mouse_move_event

        self.open_page(initial_page)

    def _rounded_mask(self, width: int, height: int, radius: int) -> QRegion:
        bitmap = QBitmap(width, height)
        bitmap.fill(Qt.color0)
        painter = QPainter(bitmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.color1)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, radius, radius)
        painter.end()
        return QRegion(bitmap)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self._container)
        root.setContentsMargins(22, 18, 22, 20)
        root.setSpacing(14)

        # -- Top Header Row (Title + Drag handle + Close) --
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        self._title = QLabel("Better It  •  Settings")
        self._title.setObjectName("SettingsTitle")
        self._title.mousePressEvent = self._mouse_press_event
        self._title.mouseMoveEvent = self._mouse_move_event
        header_row.addWidget(self._title)

        header_row.addStretch(1)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("CloseButton")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.clicked.connect(self.close)
        header_row.addWidget(self._close_btn)

        root.addLayout(header_row)

        # -- Body: Left Sidebar + Right Stacked Pages --
        body_row = QHBoxLayout()
        body_row.setSpacing(14)

        self._sidebar = QListWidget()
        self._sidebar.setObjectName("Sidebar")
        self._sidebar.setFixedWidth(160)
        for label, _ in self.PAGES:
            self._sidebar.addItem(QListWidgetItem(label))
        body_row.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._edit_tag_page = EditTagPage(self._tag_store)
        self._general_page = GeneralSettingsPage(self._tag_store)
        self._ai_model_page = AIModelPage(self._tag_store)

        self._stack.addWidget(self._edit_tag_page)   # index 0
        self._stack.addWidget(self._general_page)    # index 1
        self._stack.addWidget(self._ai_model_page)   # index 2

        body_row.addWidget(self._stack, 1)
        root.addLayout(body_row, 1)

    def _wire_signals(self) -> None:
        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)
        self._edit_tag_page.tags_changed.connect(self._on_tags_changed)
        self._general_page.tags_changed.connect(self._on_tags_changed)

    def open_page(self, page_identifier: str) -> None:
        for idx, (label, key) in enumerate(self.PAGES):
            if page_identifier.lower() in key.lower() or page_identifier.lower() in label.lower():
                self._sidebar.setCurrentRow(idx)
                return
        self._sidebar.setCurrentRow(0)

    def _on_sidebar_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        if index == 1:
            self._general_page.refresh()

    def _on_tags_changed(self) -> None:
        self._general_page.refresh()
        self.tags_changed.emit()

    # -- Drag Support -------------------------------------------------------

    def _mouse_press_event(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def _mouse_move_event(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), CORNER_RADIUS, CORNER_RADIUS)
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
