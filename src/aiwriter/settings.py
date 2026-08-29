"""Settings / Tag-manager window for BetterIt.

Opened via the "+" button on the floating window. This is a full-size
window (bigger than the small floating panel) with a left side panel
offering "Edit Tag" and "Settings" sections, similar to a native app's
preferences window.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
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

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 480

SIDEBAR_EXTRA_STYLE = """
QListWidget#Sidebar {
    background-color: rgba(230, 245, 230, 0.9);
    border: none;
    border-radius: 16px;
    padding: 8px;
    font-family: 'Comfortaa';
    font-size: 13px;
    font-weight: 700;
}
QListWidget#Sidebar::item {
    color: #1a5a1a;
    padding: 10px 12px;
    border-radius: 10px;
    margin-bottom: 4px;
}
QListWidget#Sidebar::item:selected {
    background-color: #2e7d32;
    color: #ffffff;
}
QLabel#SectionLabel {
    color: #1a5a1a;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-family: 'Comfortaa';
}
QDialog {
    background-color: #eef7ee;
}
"""


# --- "Edit Tag" page ----------------------------------------------------

class EditTagPage(QWidget):
    """List existing tags on the left; edit the selected one's name/prompt
    on the right. Also supports creating new tags and deleting old ones."""

    tags_changed = Signal()

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store
        self._current_name: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # -- Left: tag list + New button
        left = QVBoxLayout()
        left.setSpacing(8)
        left_label = QLabel("Your Tags")
        left_label.setObjectName("SectionLabel")
        left.addWidget(left_label)

        self._list = QListWidget()
        self._list.setFixedWidth(180)
        left.addWidget(self._list, 1)

        new_btn = QPushButton("+ New Tag")
        new_btn.clicked.connect(self._on_new)
        left.addWidget(new_btn)

        layout.addLayout(left)

        # -- Right: form
        right = QVBoxLayout()
        right.setSpacing(10)

        name_label = QLabel("Tag name")
        name_label.setObjectName("SectionLabel")
        right.addWidget(name_label)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. LinkedIn Post")
        right.addWidget(self._name_edit)

        prompt_label = QLabel("Prompt")
        prompt_label.setObjectName("SectionLabel")
        right.addWidget(prompt_label)
        self._prompt_edit = QTextEdit()
        self._prompt_edit.setPlaceholderText(
            "Describe how the text should be rewritten when this tag is selected..."
        )
        right.addWidget(self._prompt_edit, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setStyleSheet(
            "QPushButton { background-color: #c0392b; }"
            "QPushButton:hover { background-color: #e74c3c; }"
        )
        self._delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch(1)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        right.addLayout(btn_row)

        layout.addLayout(right, 1)

        self._list.currentTextChanged.connect(self._on_list_selection)
        self.reload()

    # -- data plumbing ----------------------------------------------------

    def reload(self, select: str | None = None) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        names = self._store.names()
        self._list.addItems(names)
        self._list.blockSignals(False)

        target = select if select in names else (names[0] if names else None)
        if target:
            items = self._list.findItems(target, Qt.MatchExactly)
            if items:
                self._list.setCurrentItem(items[0])
                self._on_list_selection(target)
        else:
            self._on_new()

    def _on_list_selection(self, name: str) -> None:
        if not name:
            return
        self._current_name = name
        self._name_edit.setText(name)
        self._prompt_edit.setPlainText(self._store.prompt_for(name))
        self._delete_btn.setEnabled(True)

    def _on_new(self) -> None:
        self._list.clearSelection()
        self._list.setCurrentRow(-1)
        self._current_name = None
        self._name_edit.clear()
        self._prompt_edit.clear()
        self._delete_btn.setEnabled(False)
        self._name_edit.setFocus()

    def _on_save(self) -> None:
        name = self._name_edit.text().strip()
        prompt = self._prompt_edit.toPlainText().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Please give this tag a name.")
            return
        if not prompt:
            QMessageBox.warning(self, "Missing prompt", "Please write a prompt for this tag.")
            return

        clashes = any(
            existing.lower() == name.lower() and existing != self._current_name
            for existing in self._store.names()
        )
        if clashes:
            QMessageBox.warning(self, "Duplicate tag", f'A tag named "{name}" already exists.')
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
            self, "Delete tag", f'Delete the tag "{self._current_name}"?'
        )
        if confirm != QMessageBox.Yes:
            return
        if self._store.delete(self._current_name):
            self._current_name = None
            self.reload()
            self.tags_changed.emit()
        else:
            QMessageBox.information(self, "Can't delete", "At least one tag must remain.")


# --- "Settings" page ------------------------------------------------------

class GeneralSettingsPage(QWidget):
    """App-wide settings: default tag, always-on-top, reset tags."""

    tags_changed = Signal()

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("General")
        title.setObjectName("SectionLabel")
        layout.addWidget(title)

        default_row = QHBoxLayout()
        default_row.addWidget(QLabel("Default tag when the window opens:"))
        self._default_combo = QComboBox()
        self._default_combo.addItems(self._store.names())
        default_row.addWidget(self._default_combo, 1)
        layout.addLayout(default_row)

        self._always_on_top = QCheckBox("Keep the floating window always on top")
        self._always_on_top.setChecked(True)
        layout.addWidget(self._always_on_top)

        layout.addStretch(1)

        reset_row = QHBoxLayout()
        reset_row.addStretch(1)
        reset_btn = QPushButton("Reset tags to defaults")
        reset_btn.clicked.connect(self._on_reset)
        reset_row.addWidget(reset_btn)
        layout.addLayout(reset_row)

    def refresh(self) -> None:
        current = self._default_combo.currentText()
        self._default_combo.clear()
        names = self._store.names()
        self._default_combo.addItems(names)
        if current in names:
            self._default_combo.setCurrentText(current)

    def _on_reset(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Reset tags",
            "This replaces all your tags with the built-in defaults. Continue?",
        )
        if confirm != QMessageBox.Yes:
            return
        self._store.reset_to_defaults()
        self.refresh()
        self.tags_changed.emit()


# --- Settings window --------------------------------------------------------

class SettingsWindow(QDialog):
    """A bigger window with a left side panel ('Edit Tag', 'Settings')."""

    tags_changed = Signal()

    PAGES = ["Edit Tag", "Settings"]

    def __init__(
        self,
        tag_store: TagStore,
        parent: QWidget | None = None,
        initial_page: str = "Edit Tag",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Better It — Settings")
        self.setStyleSheet(STYLESHEET + SIDEBAR_EXTRA_STYLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        self._sidebar = QListWidget()
        self._sidebar.setObjectName("Sidebar")
        self._sidebar.setFixedWidth(160)
        for page_name in self.PAGES:
            self._sidebar.addItem(QListWidgetItem(page_name))
        root.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._edit_tag_page = EditTagPage(tag_store)
        self._settings_page = GeneralSettingsPage(tag_store)
        self._stack.addWidget(self._edit_tag_page)
        self._stack.addWidget(self._settings_page)
        root.addWidget(self._stack, 1)

        self._sidebar.currentRowChanged.connect(self._on_page_changed)

        self._edit_tag_page.tags_changed.connect(self._on_tags_changed)
        self._settings_page.tags_changed.connect(self._on_tags_changed)

        index = self.PAGES.index(initial_page) if initial_page in self.PAGES else 0
        self._sidebar.setCurrentRow(index)

    def open_page(self, page_name: str) -> None:
        if page_name in self.PAGES:
            self._sidebar.setCurrentRow(self.PAGES.index(page_name))

    def _on_page_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        if index == 1:
            self._settings_page.refresh()

    def _on_tags_changed(self) -> None:
        self._settings_page.refresh()
        self.tags_changed.emit()
