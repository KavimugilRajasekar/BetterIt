"""Settings and Tag Manager window for BetterIt.

Follows BetterIt's signature aesthetic: frameless window with translucent mint/green
backdrop, 3px dark border, fully rounded corners, draggable custom header bar,
spacious cards, rounded interactive controls, animated pipeline, and themed popups.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from PySide6.QtCore import QByteArray, QObject, QPoint, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import (
    QBitmap,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRegion,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtSvg import QSvgRenderer
    _HAS_SVG = True
except ImportError:
    _HAS_SVG = False

try:
    from .llm import test_reachability
    from .tag_store import DEFAULT_TAGS, TagStore
    from .theme import STYLESHEET
except ImportError:
    from llm import test_reachability
    from tag_store import DEFAULT_TAGS, TagStore
    from theme import STYLESHEET

WINDOW_WIDTH = 780
WINDOW_HEIGHT = 560
CORNER_RADIUS = 28
POPUP_CORNER_RADIUS = 24


# ---------------------------------------------------------------------------
# Outlined SVG Icon factory
# ---------------------------------------------------------------------------
# All icons follow Material Icons Outlined style:
#   stroke-based, no filled areas, rounded caps, dark (#1a1a1a) strokes.

_SVG_ICONS: dict[str, str] = {
    "trash": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6l-1 14H6L5 6"/>
        <path d="M10 11v6M14 11v6"/>
        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
    </svg>""",

    "play": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <polygon points="10 8 16 12 10 16" fill="{color}" stroke="none"/>
    </svg>""",

    "loading": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2.5" stroke-linecap="round">
        <path d="M12 2a10 10 0 0 1 10 10" opacity="1"/>
        <path d="M22 12a10 10 0 0 1-10 10" opacity="0.7"/>
        <path d="M12 22a10 10 0 0 1-10-10" opacity="0.4"/>
        <path d="M2 12a10 10 0 0 1 10-10" opacity="0.15"/>
    </svg>""",

    "check": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="8 12 11 15 16 9"/>
    </svg>""",

    "arrow_right": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 18l6-6-6-6"/>
    </svg>""",

    "eye": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
        <circle cx="12" cy="12" r="3"/>
    </svg>""",

    "eye_off": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
        <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>""",

    "save": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
        <polyline points="17 21 17 13 7 13 7 21"/>
        <polyline points="7 3 7 8 15 8"/>
    </svg>""",

    "add_folder": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        <line x1="12" y1="11" x2="12" y2="17"/>
        <line x1="9" y1="14" x2="15" y2="14"/>
    </svg>""",

    "key": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
    </svg>""",

    "cpu": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="16" height="16" rx="2"/>
        <rect x="9" y="9" width="6" height="6"/>
        <line x1="9" y1="1" x2="9" y2="4"/>
        <line x1="15" y1="1" x2="15" y2="4"/>
        <line x1="9" y1="20" x2="9" y2="23"/>
        <line x1="15" y1="20" x2="15" y2="23"/>
        <line x1="20" y1="9" x2="23" y2="9"/>
        <line x1="20" y1="14" x2="23" y2="14"/>
        <line x1="1" y1="9" x2="4" y2="9"/>
        <line x1="1" y1="14" x2="4" y2="14"/>
    </svg>""",

    "profile": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
    </svg>""",

    "add_profile": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="8.5" cy="7" r="4"/>
        <line x1="20" y1="8" x2="20" y2="14"/>
        <line x1="23" y1="11" x2="17" y2="11"/>
    </svg>""",
}


def _svg_icon(name: str, color: str = "#1a1a1a", size: int = 16) -> QIcon:
    """Render an outlined SVG icon to a QIcon at the given pixel size and color."""
    svg_str = _SVG_ICONS.get(name, "")
    if not svg_str:
        return QApplication.style().standardIcon(QStyle.SP_FileIcon)

    svg_bytes = QByteArray(svg_str.format(color=color).encode("utf-8"))

    if _HAS_SVG:
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    else:
        # Fallback to Qt standard icons if SVG renderer unavailable
        fallback_map = {
            "trash": QStyle.SP_TrashIcon,
            "play": QStyle.SP_MediaPlay,
            "check": QStyle.SP_DialogApplyButton,
            "save": QStyle.SP_DialogSaveButton,
            "arrow_right": QStyle.SP_ArrowRight,
            "add_folder": QStyle.SP_FileDialogNewFolder,
        }
        sp = fallback_map.get(name, QStyle.SP_FileIcon)
        return QApplication.style().standardIcon(sp)


def _icon_btn(
    icon_name: str,
    tooltip: str,
    size: int = 28,
    color: str = "#1a1a1a",
    object_name: str = "IconButton",
) -> QPushButton:
    """Factory: small square QPushButton with outlined SVG icon."""
    btn = QPushButton()
    btn.setObjectName(object_name)
    btn.setFixedSize(size, size)
    btn.setToolTip(tooltip)
    btn.setIcon(_svg_icon(icon_name, color=color, size=size - 6))
    btn.setIconSize(QSize(size - 6, size - 6))
    return btn


# ---------------------------------------------------------------------------
# Themed Modal Popups
# ---------------------------------------------------------------------------

class ThemedDialog(QDialog):
    """A frameless, fully themed modal dialog matching BetterIt aesthetic."""

    def __init__(
        self,
        title: str,
        message: str = "",
        parent: QWidget | None = None,
        width: int = 420,
        height: int = 220,
    ) -> None:
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("ThemedDialog")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(QSize(width, height))
        self.setMask(self._rounded_mask(width, height, POPUP_CORNER_RADIUS))
        self._drag_pos: QPoint | None = None

        self._container = QWidget(self)
        self._container.setGeometry(0, 0, width, height)
        self._container.setObjectName("ThemedPopupContainer")
        self._container.setStyleSheet(STYLESHEET)

        self._root = QVBoxLayout(self._container)
        self._root.setContentsMargins(20, 16, 20, 18)
        self._root.setSpacing(12)

        header = QHBoxLayout()
        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("PopupTitle")
        header.addWidget(self._title_lbl)
        header.addStretch(1)

        self._close_btn = QPushButton("×")
        self._close_btn.setObjectName("CloseButton")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.clicked.connect(self.reject)
        header.addWidget(self._close_btn)
        self._root.addLayout(header)

        self._msg_lbl = QLabel(message)
        self._msg_lbl.setObjectName("PopupMessage")
        self._msg_lbl.setWordWrap(True)
        self._root.addWidget(self._msg_lbl, 1)

        self._btn_layout = QHBoxLayout()
        self._btn_layout.setSpacing(10)
        self._btn_layout.addStretch(1)
        self._root.addLayout(self._btn_layout)

    def _rounded_mask(self, width: int, height: int, radius: int) -> QRegion:
        bitmap = QBitmap(width, height)
        bitmap.fill(Qt.color0)
        p = QPainter(bitmap)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(Qt.color1)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, width, height, radius, radius)
        p.end()
        return QRegion(bitmap)

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


def show_themed_warning(parent, title: str, message: str) -> None:
    dlg = ThemedDialog(title, message, parent, 420, 200)
    ok = QPushButton("OK"); ok.setObjectName("Primary"); ok.setFixedHeight(36); ok.setMinimumWidth(90)
    ok.clicked.connect(dlg.accept)
    dlg._btn_layout.addWidget(ok)
    dlg.exec()


def show_themed_info(parent, title: str, message: str) -> None:
    show_themed_warning(parent, title, message)


def show_themed_confirm(parent, title: str, message: str,
                        confirm_text: str = "Yes", cancel_text: str = "No",
                        is_danger: bool = False) -> bool:
    dlg = ThemedDialog(title, message, parent, 440, 210)
    cancel = QPushButton(cancel_text); cancel.setObjectName("Secondary")
    cancel.setFixedHeight(36); cancel.setMinimumWidth(90)
    cancel.clicked.connect(dlg.reject)
    dlg._btn_layout.addWidget(cancel)
    confirm = QPushButton(confirm_text)
    confirm.setObjectName("Danger" if is_danger else "Primary")
    confirm.setFixedHeight(36); confirm.setMinimumWidth(90)
    confirm.clicked.connect(dlg.accept)
    dlg._btn_layout.addWidget(confirm)
    return dlg.exec() == QDialog.Accepted


def show_themed_input(parent, title: str, label: str,
                      default_text: str = "", placeholder: str = "") -> tuple[str, bool]:
    dlg = ThemedDialog(title, "", parent, 440, 230)
    dlg._msg_lbl.hide()
    lbl = QLabel(label); lbl.setObjectName("SubLabel"); lbl.setWordWrap(True)
    dlg._root.insertWidget(1, lbl)
    edit = QLineEdit(default_text); edit.setPlaceholderText(placeholder)
    dlg._root.insertWidget(2, edit)
    cancel = QPushButton("Cancel"); cancel.setObjectName("Secondary")
    cancel.setFixedHeight(36); cancel.setMinimumWidth(90); cancel.clicked.connect(dlg.reject)
    dlg._btn_layout.addWidget(cancel)
    ok = QPushButton("OK"); ok.setObjectName("Primary")
    ok.setFixedHeight(36); ok.setMinimumWidth(90); ok.clicked.connect(dlg.accept)
    dlg._btn_layout.addWidget(ok)
    edit.returnPressed.connect(dlg.accept); edit.setFocus()
    return edit.text().strip(), (dlg.exec() == QDialog.Accepted)


# ---------------------------------------------------------------------------
# Edit Tags Page
# ---------------------------------------------------------------------------

class EditTagPage(QWidget):
    tags_changed = Signal()

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store
        self._current_name: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        left_card = QFrame(); left_card.setObjectName("SettingsCard")
        ll = QVBoxLayout(left_card); ll.setContentsMargins(14, 14, 14, 14); ll.setSpacing(10)
        QLabel("Your Tags", objectName="SectionLabel").__class__  # noqa
        lbl = QLabel("Your Tags"); lbl.setObjectName("SectionLabel"); ll.addWidget(lbl)
        self._list = QListWidget(); self._list.setObjectName("TagList"); self._list.setFixedWidth(190)
        ll.addWidget(self._list, 1)
        nb = QPushButton("+ New Tag"); nb.setObjectName("Secondary"); nb.setFixedHeight(38)
        nb.clicked.connect(self._on_new); ll.addWidget(nb)
        layout.addWidget(left_card)

        right_card = QFrame(); right_card.setObjectName("SettingsCard")
        rl = QVBoxLayout(right_card); rl.setContentsMargins(16, 16, 16, 16); rl.setSpacing(10)

        nl = QLabel("Tag Name"); nl.setObjectName("SectionLabel"); rl.addWidget(nl)
        self._name_edit = QLineEdit(); self._name_edit.setPlaceholderText("e.g. LinkedIn Post, Professional Email…")
        rl.addWidget(self._name_edit)

        pl = QLabel("Rewrite Prompt / Instructions"); pl.setObjectName("SectionLabel"); rl.addWidget(pl)

        vt = QHBoxLayout(); vt.setSpacing(8)
        self._raw_btn = QPushButton("Raw"); self._raw_btn.setObjectName("ViewToggle")
        self._raw_btn.setCheckable(True); self._raw_btn.setChecked(True)
        self._raw_btn.clicked.connect(self._show_raw); vt.addWidget(self._raw_btn)
        self._md_btn = QPushButton("Markdown"); self._md_btn.setObjectName("ViewToggle")
        self._md_btn.setCheckable(True)
        self._md_btn.clicked.connect(self._show_md); vt.addWidget(self._md_btn)
        vt.addStretch(1); rl.addLayout(vt)

        sub = QLabel("Define how selected text should be transformed:"); sub.setObjectName("SubLabel")
        sub.setWordWrap(True); rl.addWidget(sub)

        self._stack = QStackedWidget()
        self._prompt_edit = QTextEdit()
        self._prompt_edit.setPlaceholderText("Describe the desired style, tone and format… (Markdown supported)")
        self._prompt_edit.textChanged.connect(self._sync_preview)
        self._stack.addWidget(self._prompt_edit)
        self._preview = QTextEdit(); self._preview.setReadOnly(True)
        self._preview.setPlaceholderText("Markdown preview…")
        self._stack.addWidget(self._preview)
        rl.addWidget(self._stack, 1)

        br = QHBoxLayout(); br.setSpacing(12)
        self._del_btn = QPushButton("Delete"); self._del_btn.setObjectName("Danger")
        self._del_btn.setFixedHeight(38); self._del_btn.setMinimumWidth(90)
        self._del_btn.clicked.connect(self._on_delete); br.addWidget(self._del_btn)
        br.addStretch(1)
        self._save_btn = QPushButton("Save Tag"); self._save_btn.setObjectName("Primary")
        self._save_btn.setFixedHeight(38); self._save_btn.setMinimumWidth(110)
        self._save_btn.clicked.connect(self._on_save); br.addWidget(self._save_btn)
        rl.addLayout(br)
        layout.addWidget(right_card, 1)

        self._list.currentTextChanged.connect(self._on_select)
        self.reload()

    def _show_raw(self):
        self._raw_btn.setChecked(True); self._md_btn.setChecked(False); self._stack.setCurrentIndex(0)

    def _show_md(self):
        self._raw_btn.setChecked(False); self._md_btn.setChecked(True)
        self._sync_preview(); self._stack.setCurrentIndex(1)

    def _sync_preview(self):
        self._preview.setMarkdown(self._prompt_edit.toPlainText())

    def reload(self, select: str | None = None) -> None:
        self._list.blockSignals(True); self._list.clear()
        names = self._store.names()
        for n in names:
            it = QListWidgetItem(n); it.setData(Qt.UserRole, n); self._list.addItem(it)
        self._list.blockSignals(False)
        target = select if (select and select in names) else (names[0] if names else None)
        if target:
            for i in range(self._list.count()):
                it = self._list.item(i)
                if it.data(Qt.UserRole) == target:
                    self._list.setCurrentItem(it); self._on_select(target); break
        else:
            self._on_new()

    def _on_select(self, _):
        it = self._list.currentItem()
        if not it: return
        n = it.data(Qt.UserRole)
        if not n: return
        self._current_name = n; self._name_edit.setText(n)
        p = self._store.prompt_for(n)
        self._prompt_edit.setPlainText(p); self._preview.setMarkdown(p)
        self._del_btn.setEnabled(True)

    def _on_new(self):
        self._list.clearSelection(); self._list.setCurrentRow(-1)
        self._current_name = None; self._name_edit.clear()
        self._prompt_edit.clear(); self._preview.clear()
        self._show_raw(); self._del_btn.setEnabled(False); self._name_edit.setFocus()

    def _on_save(self):
        name = self._name_edit.text().strip()
        prompt = self._prompt_edit.toPlainText().strip()
        if not name: show_themed_warning(self, "Missing Name", "Please give this tag a name."); return
        if not prompt: show_themed_warning(self, "Missing Prompt", "Please write transformation instructions."); return
        if any(e.lower() == name.lower() and e != self._current_name for e in self._store.names()):
            show_themed_warning(self, "Duplicate Tag", f'A tag named "{name}" already exists.'); return
        if self._current_name and self._current_name != name:
            self._store.rename(self._current_name, name, prompt)
        else:
            self._store.set_tag(name, prompt)
        self.reload(select=name); self.tags_changed.emit()

    def _on_delete(self):
        if not self._current_name: return
        if not show_themed_confirm(self, "Delete Tag",
                                   f'Delete "{self._current_name}"?',
                                   "Delete", "Cancel", is_danger=True): return
        if self._store.delete(self._current_name):
            self._current_name = None; self.reload(); self.tags_changed.emit()
        else:
            show_themed_info(self, "Cannot Delete", "At least one tag must remain.")


# ---------------------------------------------------------------------------
# General Settings Page
# ---------------------------------------------------------------------------

class GeneralSettingsPage(QWidget):
    tags_changed = Signal()

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(14)

        card = QFrame(); card.setObjectName("SettingsCard")
        cl = QVBoxLayout(card); cl.setContentsMargins(18, 18, 18, 18); cl.setSpacing(16)

        t = QLabel("General Preferences"); t.setObjectName("SectionLabel"); cl.addWidget(t)

        dr = QHBoxLayout(); dr.setSpacing(12)
        dl = QLabel("Default tag on window open:"); dl.setObjectName("SubLabel"); dr.addWidget(dl)
        self._default_combo = QComboBox(); self._default_combo.setMinimumWidth(180)
        self._default_combo.currentTextChanged.connect(lambda tx: self._store.set_config("default_tag", tx) if tx else None)
        dr.addWidget(self._default_combo, 1); cl.addLayout(dr)

        self._top_check = QCheckBox("Keep the floating window always on top")
        self._top_check.setChecked(bool(self._store.get_config("always_on_top", True)))
        self._top_check.toggled.connect(lambda v: self._store.set_config("always_on_top", v))
        cl.addWidget(self._top_check)

        hk = QFrame(); hk.setObjectName("InnerCard")
        hkl = QVBoxLayout(hk); hkl.setContentsMargins(14, 12, 14, 12); hkl.setSpacing(6)
        hkl.addWidget(QLabel("Global Trigger Shortcut", objectName="SectionLabel"))
        hv = os.environ.get("HOTKEY", "Ctrl + Space")
        hd = QLabel(f"Select text and press <b>{hv}</b> to open BetterIt.<br>"
                    f"Press <b>{hv}</b> with no text to open Settings.")
        hd.setObjectName("SubLabel"); hd.setWordWrap(True); hkl.addWidget(hd)
        cl.addWidget(hk); cl.addStretch(1)

        rr = QHBoxLayout(); rr.addStretch(1)
        rb = QPushButton("Reset All Tags to Defaults"); rb.setObjectName("Secondary")
        rb.setFixedHeight(36); rb.clicked.connect(self._on_reset); rr.addWidget(rb)
        cl.addLayout(rr); layout.addWidget(card)
        self.refresh()

    def refresh(self) -> None:
        saved = self._store.get_config("default_tag", "Grammar & Clarity")
        self._default_combo.blockSignals(True); self._default_combo.clear()
        names = self._store.names(); self._default_combo.addItems(names)
        if saved in names: self._default_combo.setCurrentText(saved)
        elif names: self._default_combo.setCurrentIndex(0)
        self._default_combo.blockSignals(False)

    def _on_reset(self):
        if show_themed_confirm(self, "Reset Tags",
                               "Restore all tags to initial defaults?",
                               "Reset", "Cancel", is_danger=True):
            self._store.reset_to_defaults(); self.refresh(); self.tags_changed.emit()


# ---------------------------------------------------------------------------
# Reachability Worker
# ---------------------------------------------------------------------------

class ReachabilityWorker(QObject):
    finished = Signal(bool, str)

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__()
        self._api_key = api_key
        self._model = model

    @Slot()
    def run(self) -> None:
        success, message = test_reachability(api_key=self._api_key, model=self._model)
        self.finished.emit(success, message)


# ---------------------------------------------------------------------------
# Profile Card Widget  (solid white, outlined SVG icons, animated Test btn)
# ---------------------------------------------------------------------------

class ProfileCardWidget(QFrame):
    """
    Single solid-white card for one API Key Space.

    Header    : outlined profile icon + name + Active badge / Set-Active + trash (top-right)
    API Key   : outlined key icon + label | masked QLineEdit with eye icon inside + Save
    Models    : vertical rows — name | Active badge/Set-Active | play-Test | trash-Remove
                  Tap Test → button animates dots + grey row → green (reachable) / red (unreachable)
    Add Model : text input + add-folder btn
    Status    : black-bordered result panel
    """

    profile_changed = Signal()
    active_space_requested = Signal(str)
    delete_space_requested = Signal(str)

    def __init__(
        self,
        space_data: dict[str, Any],
        is_active: bool,
        is_only_one: bool,
        tag_store: TagStore,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._space_data = space_data
        self._space_name = str(space_data.get("name", "OpenRouter"))
        self._store = tag_store

        # Concurrency
        self._test_thread: QThread | None = None
        self._test_worker: ReachabilityWorker | None = None
        self._active_test_model: str | None = None

        # Live references to model rows + buttons
        self._model_row_frames: dict[str, QFrame] = {}
        self._test_btns: dict[str, QPushButton] = {}

        # Loading animation
        self._loading_timer = QTimer(self)
        self._loading_timer.setInterval(380)
        self._loading_dot_idx = 0
        self._loading_timer.timeout.connect(self._animate_loading)

        self._key_revealed = False

        # Card border: green if active, dark if not
        self.setObjectName("KeyProfileCard")
        self.setStyleSheet(
            "QFrame#KeyProfileCard{background:#fff;border:2.5px solid #1b5e20;border-radius:20px;}"
            if is_active else
            "QFrame#KeyProfileCard{background:#fff;border:2px solid #0a0a0a;border-radius:20px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        # ── Header ──────────────────────────────────────────────────────
        hdr = QHBoxLayout(); hdr.setSpacing(8)

        dec = _icon_btn("profile", "Profile", 30, "#1b5e20")
        dec.setEnabled(False); hdr.addWidget(dec)

        name_lbl = QLabel(self._space_name); name_lbl.setObjectName("CardTitle")
        hdr.addWidget(name_lbl)

        if is_active:
            badge = QLabel("Active Space"); badge.setObjectName("ActiveBadge")
            hdr.addWidget(badge)
        else:
            sa = QPushButton("Set Active"); sa.setObjectName("MiniAction")
            sa.setIcon(_svg_icon("check", "#1b5e20", 13)); sa.setIconSize(QSize(13, 13))
            sa.clicked.connect(lambda: self.active_space_requested.emit(self._space_name))
            hdr.addWidget(sa)

        hdr.addStretch(1)

        del_card = _icon_btn("trash", "Delete this profile", 30, "#c0392b", "DangerIcon")
        del_card.setEnabled(not is_only_one)
        del_card.clicked.connect(lambda: self.delete_space_requested.emit(self._space_name))
        hdr.addWidget(del_card)
        root.addLayout(hdr)

        # Separator
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:rgba(10,10,10,.12);max-height:1px;border:none;")
        root.addWidget(sep)

        # ── API Key ──────────────────────────────────────────────────────
        api_lbl_row = QHBoxLayout(); api_lbl_row.setSpacing(6)
        kd = _icon_btn("key", "API Key", 24, "#1b5e20"); kd.setEnabled(False)
        api_lbl_row.addWidget(kd)
        api_lbl_row.addWidget(QLabel("API Key", objectName="PaneLabel"), 1)
        root.addLayout(api_lbl_row)

        key_row = QHBoxLayout(); key_row.setSpacing(8)
        self._key_edit = QLineEdit(self._space_data.get("api_key", ""))
        self._key_edit.setEchoMode(QLineEdit.Password)
        self._key_edit.setFixedHeight(38)
        self._key_edit.setPlaceholderText("sk-or-v1-…  Paste your API key here")
        self._key_edit.textChanged.connect(
            lambda t: self._store.update_key_space(self._space_name, api_key=t.strip()))

        # Eye icon embedded inside the QLineEdit trailing side
        self._eye_action = self._key_edit.addAction(
            _svg_icon("eye", "#1b5e20", 16), QLineEdit.TrailingPosition)
        self._eye_action.setToolTip("Show / Hide key")
        self._eye_action.triggered.connect(self._toggle_eye)
        key_row.addWidget(self._key_edit, 1)

        save_k = QPushButton("Save Key"); save_k.setObjectName("Primary")
        save_k.setFixedHeight(38)
        save_k.setIcon(_svg_icon("save", "#ffffff", 14)); save_k.setIconSize(QSize(14, 14))
        save_k.clicked.connect(self._save_key)
        key_row.addWidget(save_k)
        root.addLayout(key_row)

        # ── Models list ──────────────────────────────────────────────────
        ml_row = QHBoxLayout(); ml_row.setSpacing(6)
        md = _icon_btn("cpu", "Configured Models", 24, "#1b5e20"); md.setEnabled(False)
        ml_row.addWidget(md)
        ml_row.addWidget(QLabel("Configured Models", objectName="PaneLabel"), 1)
        root.addLayout(ml_row)

        models = list(self._space_data.get("models", []))
        selected = str(self._space_data.get("selected_model", models[0] if models else ""))

        self._models_container = QVBoxLayout(); self._models_container.setSpacing(5)
        for m in models:
            self._build_model_row(m, m == selected, len(models))
        root.addLayout(self._models_container)

        # ── Add Model ────────────────────────────────────────────────────
        add_row = QHBoxLayout(); add_row.setSpacing(8)
        self._add_edit = QLineEdit()
        self._add_edit.setFixedHeight(34)
        self._add_edit.setPlaceholderText("Model ID  (e.g. google/gemini-2.5-pro, deepseek/deepseek-r1)")
        self._add_edit.returnPressed.connect(self._add_model)
        add_row.addWidget(self._add_edit, 1)
        add_btn = QPushButton("Add Model"); add_btn.setObjectName("Secondary")
        add_btn.setFixedHeight(34)
        add_btn.setIcon(_svg_icon("add_folder", "#1b5e20", 14)); add_btn.setIconSize(QSize(14, 14))
        add_btn.clicked.connect(self._add_model)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)

        # ── Status panel (black border always) ──────────────────────────
        self._status_frame = QFrame()
        self._status_frame.setFixedHeight(36)
        self._status_frame.setStyleSheet(
            "QFrame{background:#f4fff4;border:2px solid #0a0a0a;border-radius:14px;}")
        sl = QHBoxLayout(self._status_frame); sl.setContentsMargins(12, 4, 12, 4)
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(
            "border:none;background:transparent;color:#386038;"
            "font-size:11px;font-weight:600;font-family:'Comfortaa';")
        self._status_lbl.setWordWrap(False)
        sl.addWidget(self._status_lbl)
        root.addWidget(self._status_frame)

    # ── model row factory ─────────────────────────────────────────────────

    def _build_model_row(self, model_id: str, is_sel: bool, total: int) -> None:
        row = QFrame(); row.setObjectName("ModelRowFrame")
        row.setStyleSheet(
            "QFrame{background:#edfaed;border:2px solid #1b5e20;border-radius:13px;}"
            if is_sel else
            "QFrame{background:#fff;border:1.5px solid #0a0a0a;border-radius:13px;}")
        self._model_row_frames[model_id] = row

        rl = QHBoxLayout(row); rl.setContentsMargins(10, 5, 8, 5); rl.setSpacing(6)
        lbl = QLabel(model_id); lbl.setObjectName("ModelNameLabel")
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        rl.addWidget(lbl, 1)

        if is_sel:
            badge = QPushButton("Active"); badge.setObjectName("ModelActiveBadge")
            badge.setIcon(_svg_icon("check", "#ffffff", 12)); badge.setIconSize(QSize(12, 12))
            badge.setEnabled(False); badge.setFixedHeight(25); rl.addWidget(badge)
        else:
            sa = QPushButton("Set Active"); sa.setObjectName("MiniAction")
            sa.setIcon(_svg_icon("arrow_right", "#1b5e20", 12)); sa.setIconSize(QSize(12, 12))
            sa.setFixedHeight(25)
            sa.clicked.connect(lambda _, m=model_id: self._set_active_model(m))
            rl.addWidget(sa)

        # Test button — play icon
        test_btn = QPushButton("Test"); test_btn.setObjectName("ModelTestBtn")
        test_btn.setIcon(_svg_icon("play", "#ffffff", 12)); test_btn.setIconSize(QSize(12, 12))
        test_btn.setFixedHeight(25)
        test_btn.clicked.connect(lambda _, m=model_id: self._run_test(m))
        rl.addWidget(test_btn)
        self._test_btns[model_id] = test_btn

        # Trash icon
        del_btn = _icon_btn("trash", "Remove model", 25, "#c0392b", "DangerIcon")
        del_btn.setEnabled(total > 1)
        del_btn.clicked.connect(lambda _, m=model_id: self._del_model(m))
        rl.addWidget(del_btn)

        self._models_container.addWidget(row)

    # ── helpers ───────────────────────────────────────────────────────────

    def _toggle_eye(self) -> None:
        self._key_revealed = not self._key_revealed
        if self._key_revealed:
            self._key_edit.setEchoMode(QLineEdit.Normal)
            self._eye_action.setIcon(_svg_icon("eye_off", "#1b5e20", 16))
        else:
            self._key_edit.setEchoMode(QLineEdit.Password)
            self._eye_action.setIcon(_svg_icon("eye", "#1b5e20", 16))

    def _save_key(self) -> None:
        self._store.update_key_space(self._space_name, api_key=self._key_edit.text().strip())
        self._set_status("API key saved.", ok=True)

    def _set_active_model(self, model_id: str) -> None:
        self._store.update_key_space(self._space_name, selected_model=model_id)
        self.profile_changed.emit()

    def _del_model(self, model_id: str) -> None:
        if self._store.delete_model_from_space(self._space_name, model_id):
            self.profile_changed.emit()

    def _add_model(self) -> None:
        mid = self._add_edit.text().strip()
        if not mid:
            self._set_status("Please enter a model ID first.", ok=False); return
        self._store.add_model_to_space(self._space_name, mid)
        self._add_edit.clear(); self.profile_changed.emit()

    def _set_status(self, text: str, ok: bool | None = None) -> None:
        self._status_lbl.setText(text)
        if ok is True:
            self._status_frame.setStyleSheet(
                "QFrame{background:#e8f8e8;border:2px solid #0a0a0a;border-radius:14px;}")
            self._status_lbl.setStyleSheet(
                "border:none;background:transparent;color:#1b5e20;"
                "font-size:11px;font-weight:700;font-family:'Comfortaa';")
        elif ok is False:
            self._status_frame.setStyleSheet(
                "QFrame{background:#fde8e8;border:2px solid #0a0a0a;border-radius:14px;}")
            self._status_lbl.setStyleSheet(
                "border:none;background:transparent;color:#c0392b;"
                "font-size:11px;font-weight:700;font-family:'Comfortaa';")
        else:
            self._status_frame.setStyleSheet(
                "QFrame{background:#f4fff4;border:2px solid #0a0a0a;border-radius:14px;}")
            self._status_lbl.setStyleSheet(
                "border:none;background:transparent;color:#386038;"
                "font-size:11px;font-weight:600;font-family:'Comfortaa';")

    # ── test flow ─────────────────────────────────────────────────────────

    def _animate_loading(self) -> None:
        btn = self._test_btns.get(self._active_test_model or "")
        if not btn:
            return
        frames = ["   ", ".  ", ".. ", "..."]
        self._loading_dot_idx = (self._loading_dot_idx + 1) % len(frames)
        btn.setText(f"Testing{frames[self._loading_dot_idx]}")

    def _run_test(self, model_id: str) -> None:
        api_key = self._key_edit.text().strip()
        if not api_key:
            self._set_status("Error: Enter an API key above to test.", ok=False)
            return

        # Animate the Test button
        btn = self._test_btns.get(model_id)
        if btn:
            btn.setEnabled(False)
            btn.setText("Testing   ")
            btn.setIcon(_svg_icon("loading", "#ffffff", 12))

        # Grey the row while in-flight
        row = self._model_row_frames.get(model_id)
        if row:
            row.setStyleSheet(
                "QFrame{background:#f5f5f5;border:2px solid #aaa;border-radius:13px;}")

        self._active_test_model = model_id
        self._loading_dot_idx = 0
        self._loading_timer.start()
        self._set_status(f"Connecting to OpenRouter  ({model_id})\u2026")

        self._test_thread = QThread()
        self._test_worker = ReachabilityWorker(api_key, model_id)
        self._test_worker.moveToThread(self._test_thread)
        self._test_thread.started.connect(self._test_worker.run)
        self._test_worker.finished.connect(self._on_result, Qt.QueuedConnection)
        self._test_worker.finished.connect(self._test_thread.quit)
        self._test_thread.finished.connect(self._test_worker.deleteLater)
        self._test_thread.finished.connect(self._test_thread.deleteLater)
        self._test_thread.start()

    @Slot(bool, str)
    def _on_result(self, success: bool, message: str) -> None:
        self._loading_timer.stop()
        mid = self._active_test_model
        self._active_test_model = None

        # Restore Test button
        btn = self._test_btns.get(mid or "")
        if btn:
            btn.setEnabled(True)
            btn.setText("Test")
            btn.setIcon(_svg_icon("play", "#ffffff", 12))

        # Colour the model row green or red
        row = self._model_row_frames.get(mid or "")
        if row:
            if success:
                row.setStyleSheet(
                    "QFrame{background:#d4f8d4;border:2.5px solid #1b5e20;border-radius:13px;}")
            else:
                row.setStyleSheet(
                    "QFrame{background:#fdd8d8;border:2.5px solid #c0392b;border-radius:13px;}")

        if success:
            self._set_status(f"Reachable  \u2014  {message}", ok=True)
        else:
            self._set_status(f"Unreachable  \u2014  {message}", ok=False)


# ---------------------------------------------------------------------------
# Inline New-Profile Card  (no popups)
# ---------------------------------------------------------------------------

class NewProfileCardWidget(QFrame):
    created = Signal()

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store
        self._is_expanded = False
        self.setObjectName("NewProfileCard")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(10)

        self._open_btn = QPushButton("Add New Profile")
        self._open_btn.setObjectName("Secondary")
        self._open_btn.setFixedHeight(40)
        self._open_btn.setIcon(_svg_icon("add_profile", "#1b5e20", 16))
        self._open_btn.setIconSize(QSize(16, 16))
        self._open_btn.clicked.connect(self._expand)
        self._layout.addWidget(self._open_btn)

        self._form = QWidget()
        fl = QVBoxLayout(self._form); fl.setContentsMargins(0, 0, 0, 0); fl.setSpacing(8)

        t = QLabel("Create New Profile Space"); t.setObjectName("CardTitle"); fl.addWidget(t)

        nl = QLabel("Profile Name"); nl.setObjectName("SubLabel"); fl.addWidget(nl)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Work Key, High Performance, Fast & Cheap…")
        fl.addWidget(self._name_edit)

        kl = QLabel("API Key  (optional, can be added later)"); kl.setObjectName("SubLabel")
        fl.addWidget(kl)
        self._key_edit = QLineEdit(); self._key_edit.setEchoMode(QLineEdit.Password)
        self._key_edit.setPlaceholderText("sk-or-v1-…")
        fl.addWidget(self._key_edit)

        self._err_lbl = QLabel(""); self._err_lbl.setObjectName("SubLabel"); fl.addWidget(self._err_lbl)

        br = QHBoxLayout(); br.setSpacing(8)
        cancel = QPushButton("Cancel"); cancel.setObjectName("Secondary")
        cancel.setFixedHeight(34); cancel.clicked.connect(self._collapse); br.addWidget(cancel)
        br.addStretch(1)
        create = QPushButton("Create Profile"); create.setObjectName("Primary")
        create.setFixedHeight(34)
        create.setIcon(_svg_icon("add_profile", "#ffffff", 14)); create.setIconSize(QSize(14, 14))
        create.clicked.connect(self._create); br.addWidget(create)
        fl.addLayout(br)

        self._layout.addWidget(self._form)
        self._form.hide()

    def _expand(self) -> None:
        self._is_expanded = True
        self._open_btn.hide()
        self._name_edit.clear(); self._key_edit.clear(); self._err_lbl.setText("")
        self._form.show(); self._name_edit.setFocus()

    def _collapse(self) -> None:
        self._is_expanded = False
        self._form.hide(); self._open_btn.show()

    def _create(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            self._err_lbl.setStyleSheet("color:#c0392b;font-weight:700;font-family:'Comfortaa';font-size:11px;")
            self._err_lbl.setText("Please enter a profile name."); return
        if name.lower() in [s.lower() for s in self._store.get_key_space_names()]:
            self._err_lbl.setStyleSheet("color:#c0392b;font-weight:700;font-family:'Comfortaa';font-size:11px;")
            self._err_lbl.setText(f'Profile "{name}" already exists.'); return
        self._store.add_key_space(name, api_key=self._key_edit.text().strip())
        self._collapse(); self.created.emit()


# ---------------------------------------------------------------------------
# AI Model Page
# ---------------------------------------------------------------------------

class AIModelPage(QWidget):
    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store

        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget(); self._content.setStyleSheet("background:transparent;")
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(4, 4, 10, 8); self._layout.setSpacing(14)

        scroll.setWidget(self._content); outer.addWidget(scroll)
        self.reload()

    def reload(self) -> None:
        while self._layout.count():
            it = self._layout.takeAt(0)
            if it.widget(): it.widget().deleteLater()

        hdr = QLabel("AI Profile Spaces & Models"); hdr.setObjectName("SectionLabel")
        self._layout.addWidget(hdr)

        spaces = self._store.get_key_spaces()
        active = self._store.get_active_key_space_name()
        only_one = len(spaces) <= 1

        for space in spaces:
            name = str(space.get("name", "OpenRouter"))
            card = ProfileCardWidget(space, name == active, only_one, self._store)
            card.profile_changed.connect(self.reload)
            card.active_space_requested.connect(self._set_active)
            card.delete_space_requested.connect(self._delete_space)
            self._layout.addWidget(card)

        new_card = NewProfileCardWidget(self._store)
        new_card.created.connect(self.reload)
        self._layout.addWidget(new_card)
        self._layout.addStretch(1)

    def _set_active(self, name: str) -> None:
        self._store.set_active_key_space_name(name); self.reload()

    def _delete_space(self, name: str) -> None:
        if self._store.delete_key_space(name): self.reload()


# ---------------------------------------------------------------------------
# About Page  (animated pipeline)
# ---------------------------------------------------------------------------

class AboutPage(QWidget):
    STEPS = [
        ("1", "Select Text",       "Highlight any text in any app, browser, or chat window."),
        ("2", "Press Ctrl+Space",  "The BetterIt window opens instantly with your transformation tags."),
        ("3", "Pick a Tag",        "Choose a preset or your own custom tag — Professional, LinkedIn, Chat, etc."),
        ("4", "Polish with AI",    "Click Polish (Ctrl+Enter). OpenRouter AI rewrites per the tag's instructions."),
        ("5", "Copy or Replace",   "Copy the improved text, or hit Replace to paste it back into your app."),
        ("6", "Configure Anytime", "Open Settings to create tags, manage API key profiles, and test models."),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active = 0
        self._frames: list[QFrame] = []

        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget(); content.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 8, 0); cl.setSpacing(12)

        # Hero
        hero = QFrame(); hero.setObjectName("AboutHeroCard")
        hl = QVBoxLayout(hero); hl.setContentsMargins(20, 16, 20, 16); hl.setSpacing(8)
        hr = QHBoxLayout()
        hn = QLabel("Better It"); hn.setObjectName("AboutHeroLabel"); hr.addWidget(hn)
        hr.addStretch(1)
        hb = QLabel("AI Writing Companion")
        hb.setStyleSheet("background:#1b5e20;color:#fff;border-radius:12px;padding:4px 12px;"
                         "font-weight:700;font-size:11px;font-family:'Comfortaa';")
        hr.addWidget(hb); hl.addLayout(hr)
        ht = QLabel("Select any text on screen, tap a shortcut, transform your words.")
        ht.setObjectName("SubLabel"); ht.setWordWrap(True); hl.addWidget(ht)
        hv = QLabel("BetterIt v1.2  •  OpenRouter  •  PySide6")
        hv.setObjectName("AboutVersion"); hl.addWidget(hv)
        cl.addWidget(hero)

        # Pipeline
        pc = QFrame(); pc.setObjectName("SettingsCard")
        pl = QVBoxLayout(pc); pl.setContentsMargins(18, 16, 18, 16); pl.setSpacing(8)
        ph = QHBoxLayout()
        ph.addWidget(QLabel("Execution Pipeline", objectName="SectionLabel"))
        ph.addStretch(1)
        ph.addWidget(QLabel("Live Pipeline", objectName="AboutVersion"))
        pl.addLayout(ph)

        for i, (num, name, desc) in enumerate(self.STEPS):
            sf = QFrame(); sf.setObjectName("AboutStepCard")
            sfl = QHBoxLayout(sf); sfl.setContentsMargins(14, 10, 14, 10); sfl.setSpacing(12)
            ico = QLabel(num); ico.setFixedSize(36, 36); ico.setAlignment(Qt.AlignCenter)
            ico.setStyleSheet("background:#2e7d32;color:#fff;border-radius:18px;"
                              "font-size:14px;font-weight:700;border:2px solid #0a0a0a;")
            sfl.addWidget(ico)
            tc = QVBoxLayout(); tc.setSpacing(2)
            tc.addWidget(QLabel(f"Step {num}  •  {name}", objectName="AboutStepLabel"))
            dl = QLabel(desc); dl.setObjectName("AboutStepDesc"); dl.setWordWrap(True)
            tc.addWidget(dl); sfl.addLayout(tc, 1)
            pl.addWidget(sf); self._frames.append(sf)
            if i < len(self.STEPS) - 1:
                arr = QLabel("↓"); arr.setAlignment(Qt.AlignHCenter)
                arr.setStyleSheet("color:#2e7d32;font-size:14px;font-weight:700;")
                pl.addWidget(arr)
        cl.addWidget(pc)

        # Tips
        tc2 = QFrame(); tc2.setObjectName("InnerCard")
        tl = QVBoxLayout(tc2); tl.setContentsMargins(16, 14, 16, 14); tl.setSpacing(8)
        tl.addWidget(QLabel("Tips & Shortcuts", objectName="SectionLabel"))
        for tip in [
            "Press <b>Ctrl+Space</b> with no text to open Settings directly.",
            "Click <b>–</b> to minimize BetterIt into a floating pencil ball.",
            "Configure multiple <b>Key Spaces</b> for personal vs work API keys.",
            "All rewrite instructions come strictly from tags you configure.",
            "Unreadable text returns <i>'This Was Jumpled Words: NOT MAKE SENSE'</i>.",
        ]:
            rw = QHBoxLayout(); rw.setSpacing(8)
            dot = QLabel("*"); dot.setStyleSheet("color:#1b5e20;font-size:14px;font-weight:700;")
            dot.setFixedWidth(14); rw.addWidget(dot)
            tl2 = QLabel(tip); tl2.setObjectName("AboutStepDesc"); tl2.setWordWrap(True)
            rw.addWidget(tl2, 1); tl.addLayout(rw)
        cl.addWidget(tc2); cl.addStretch(1)
        scroll.setWidget(content); outer.addWidget(scroll)

        self._timer = QTimer(self); self._timer.setInterval(2200)
        self._timer.timeout.connect(self._step); self._timer.start()
        self._highlight()

    def _step(self):
        self._active = (self._active + 1) % len(self._frames); self._highlight()

    def _highlight(self):
        for i, f in enumerate(self._frames):
            if i == self._active:
                f.setStyleSheet("background:rgba(220,250,220,.98);border:2.5px solid #1b5e20;border-radius:18px;")
            else:
                f.setStyleSheet("background:rgba(255,255,255,.75);border:1.5px solid rgba(10,10,10,.3);border-radius:18px;")


# ---------------------------------------------------------------------------
# BallWidget (minimised floating ball)
# ---------------------------------------------------------------------------

class BallWidget(QWidget):
    expand_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(QSize(62, 62))
        self._drag_pos: QPoint | None = None
        self._press_pos: QPoint | None = None
        self._dragging = False

    def show_at(self, pos: QPoint) -> None:
        self.move(pos); self.show(); self.raise_()

    def paintEvent(self, event) -> None:
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(3, 3, -3, -3)
        p.setBrush(QBrush(QColor("#1b5e20")))
        p.setPen(QPen(QColor("#0a0a0a"), 2.5))
        p.drawEllipse(rect)
        p.setPen(QPen(QColor("#ffffff")))
        f = QFont("Comfortaa", 18); f.setBold(True); p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, "P")   # P for Pencil, no emoji
        p.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._press_pos = event.globalPosition().toPoint()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            cur = event.globalPosition().toPoint()
            if self._press_pos and (cur - self._press_pos).manhattanLength() > 5:
                self._dragging = True
            delta = cur - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = cur
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and not self._dragging:
            self.expand_requested.emit()
        self._drag_pos = self._press_pos = None; self._dragging = False
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
# Settings Window
# ---------------------------------------------------------------------------

class SettingsWindow(QDialog):
    tags_changed = Signal()
    minimize_requested = Signal()

    PAGES = [("Edit Tags", "Edit Tag"), ("General", "General"),
             ("AI Model", "AI Model"), ("About", "About")]

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
        self.setMask(self._mask(WINDOW_WIDTH, WINDOW_HEIGHT, CORNER_RADIUS))

        self._store = tag_store
        self._drag_pos: QPoint | None = None
        self._ball: BallWidget | None = None

        self._container = QWidget(self)
        self._container.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self._container.setObjectName("SettingsWindow")
        self._container.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._sidebar.currentRowChanged.connect(self._on_page)
        self._edit_tag_page.tags_changed.connect(self._on_tags)
        self._general_page.tags_changed.connect(self._on_tags)
        self._container.mousePressEvent = lambda e: self._drag_start(e)
        self._container.mouseMoveEvent = lambda e: self._drag_move(e)
        self.open_page(initial_page)

    def _mask(self, w, h, r) -> QRegion:
        bm = QBitmap(w, h); bm.fill(Qt.color0)
        p = QPainter(bm); p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(Qt.color1); p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, w, h, r, r); p.end()
        return QRegion(bm)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self._container)
        root.setContentsMargins(22, 18, 22, 20); root.setSpacing(14)

        hdr = QHBoxLayout(); hdr.setSpacing(8)
        self._title = QLabel("Better It  •  Settings"); self._title.setObjectName("SettingsTitle")
        hdr.addWidget(self._title); hdr.addStretch(1)

        self._min_btn = QPushButton("–"); self._min_btn.setObjectName("MinimizeButton")
        self._min_btn.setFixedSize(30, 30); self._min_btn.setToolTip("Minimize to ball")
        self._min_btn.clicked.connect(self._on_minimize); hdr.addWidget(self._min_btn)

        self._close_btn = QPushButton("×"); self._close_btn.setObjectName("CloseButton")
        self._close_btn.setFixedSize(30, 30); self._close_btn.clicked.connect(self.close)
        hdr.addWidget(self._close_btn); root.addLayout(hdr)

        body = QHBoxLayout(); body.setSpacing(14)
        self._sidebar = QListWidget(); self._sidebar.setObjectName("Sidebar")
        self._sidebar.setFixedWidth(160)
        for label, _ in self.PAGES:
            self._sidebar.addItem(QListWidgetItem(label))
        body.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._edit_tag_page = EditTagPage(self._store)
        self._general_page = GeneralSettingsPage(self._store)
        self._ai_page = AIModelPage(self._store)
        self._about_page = AboutPage()
        for page in (self._edit_tag_page, self._general_page, self._ai_page, self._about_page):
            self._stack.addWidget(page)
        body.addWidget(self._stack, 1); root.addLayout(body, 1)

    def open_page(self, identifier: str) -> None:
        for idx, (label, key) in enumerate(self.PAGES):
            if identifier.lower() in key.lower() or identifier.lower() in label.lower():
                self._sidebar.setCurrentRow(idx); return
        self._sidebar.setCurrentRow(0)

    def _on_page(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        if idx == 1: self._general_page.refresh()
        elif idx == 2: self._ai_page.reload()

    def _on_tags(self) -> None:
        self._general_page.refresh(); self.tags_changed.emit()

    def _on_minimize(self) -> None:
        center = self.geometry().center()
        ball_pos = QPoint(center.x() - 31, center.y() - 31)
        self.hide()
        if self._ball is None:
            self._ball = BallWidget()
            self._ball.expand_requested.connect(self._on_ball_expand)
        self._ball.show_at(ball_pos); self.minimize_requested.emit()

    def _on_ball_expand(self) -> None:
        if self._ball:
            bc = self._ball.geometry().center()
            self._ball.hide()
            self.move(bc.x() - self.width() // 2, bc.y() - self.height() // 2)
        if (sc := self.screen()):
            g = sc.availableGeometry(); p = self.pos()
            p.setX(max(0, min(p.x(), g.right() - self.width())))
            p.setY(max(0, min(p.y(), g.bottom() - self.height())))
            self.move(p)
        self.show(); self.raise_(); self.activateWindow()

    def _drag_start(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def _drag_move(self, event: QMouseEvent) -> None:
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mousePressEvent(self, e): self._drag_start(e); super().mousePressEvent(e)
    def mouseMoveEvent(self, e): self._drag_move(e); super().mouseMoveEvent(e)
    def mouseReleaseEvent(self, e): self._drag_pos = None; super().mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape: self.close(); e.accept(); return
        super().keyPressEvent(e)

    def paintEvent(self, event) -> None:
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), CORNER_RADIUS, CORNER_RADIUS)
        p.setBrush(QBrush(QColor(0, 0, 0, 0))); p.setPen(Qt.NoPen)
        p.drawPath(path); p.end()
