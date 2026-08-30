"""Settings and Tag Manager window for BetterIt.

Follows BetterIt's signature aesthetic: frameless window with translucent mint/green
backdrop, 3px dark border, fully rounded corners, draggable custom header bar,
spacious cards, rounded interactive controls, animated pipeline, and themed popups.
"""

from __future__ import annotations

import os
from pathlib import Path
from . import get_resource_path
from typing import Any, Optional

from PySide6.QtCore import (
    QByteArray, QEasingCurve, QObject, QPoint, QPropertyAnimation, QRect,
    QSize, Qt, QThread, QTimer, QVariantAnimation, Signal, Slot,
)
from PySide6.QtGui import (
    QBitmap,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QImage,
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
    QGraphicsOpacityEffect,
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
    "expand": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="15 3 21 3 21 9"/>
        <polyline points="9 21 3 21 3 15"/>
        <line x1="21" y1="3" x2="14" y2="10"/>
        <line x1="3" y1="21" x2="10" y2="14"/>
    </svg>""",

    "shrink": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="4 14 10 14 10 20"/>
        <polyline points="20 10 14 10 14 4"/>
        <line x1="14" y1="10" x2="21" y2="3"/>
        <line x1="10" y1="14" x2="3" y2="21"/>
    </svg>""",

    "return": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 14L4 9l5-5"/>
        <path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5v0a5.5 5.5 0 0 1-5.5 5.5H11"/>
    </svg>""",

    "trash": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6l-1 14H6L5 6"/>
        <path d="M10 11v6M14 11v6"/>
        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
    </svg>""",

    "circle_outline": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
        stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
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


def _load_png_icon(name: str, size: int) -> QIcon | None:
    """Load specific PNG assets cleanly, falling back to None if not found/applicable."""
    filename = "test.png" if name == "play" else "delete.png" if name == "trash" else None
    if filename:
        path = get_resource_path(os.path.join("assets", filename))
        if os.path.exists(path):
            pixmap = QPixmap(path)
            return QIcon(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return None


def _svg_icon(name: str, color: str = "#1a1a1a", size: int = 16) -> QIcon:
    """Render an outlined SVG icon to a QIcon, loading custom PNGs for play/trash if available."""
    png = _load_png_icon(name, size)
    if png:
        return png

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


class HoverIconButton(QPushButton):
    """QPushButton that swaps icons smoothly on mouse enter / leave."""
    def __init__(self, normal_icon: QIcon, hover_icon: QIcon, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._normal_icon = normal_icon
        self._hover_icon = hover_icon
        self.setIcon(self._normal_icon)

    def enterEvent(self, event) -> None:
        if not self._hover_icon.isNull():
            self.setIcon(self._hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if not self._normal_icon.isNull():
            self.setIcon(self._normal_icon)
        super().leaveEvent(event)


class QuickReplaceToast(QFrame):
    """
    A self-dismissing error toast that appears centred over `parent_window`,
    stays for 3 seconds, then fades out and destroys itself.

    Usage::
        QuickReplaceToast.show_error(parent_window, "Cannot replace: LLM returned garbled output.")
    """

    def __init__(self, parent_window: QWidget, message: str) -> None:
        super().__init__(parent_window)
        self.setObjectName("QuickReplaceToastFrame")
        self.setStyleSheet("""
            QFrame#QuickReplaceToastFrame {
                background-color: #1a1a1a;
                border: 1.5px solid #444444;
                border-radius: 14px;
            }
            QLabel { color: #ffffff; font-size: 13px; font-family: 'Comfortaa'; }
        """)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFixedWidth(340)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(6)

        # Warning icon row
        top_row = QHBoxLayout()
        icon_lbl = QLabel("⚠")
        icon_lbl.setStyleSheet(
            "color: #f0a500; font-size: 20px; font-family: 'Comfortaa'; padding-right: 4px;"
        )
        top_row.addWidget(icon_lbl)
        title_lbl = QLabel("Quick Replace Failed")
        title_lbl.setStyleSheet(
            "color: #ffffff; font-size: 13px; font-weight: 700; font-family: 'Comfortaa';"
        )
        top_row.addWidget(title_lbl, 1)
        lay.addLayout(top_row)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(
            "color: #cccccc; font-size: 12px; font-family: 'Comfortaa';"
        )
        lay.addWidget(msg_lbl)

        self.adjustSize()

        # Position: centred horizontally, 20% from top of parent
        pw = parent_window
        cx = pw.width() // 2 - self.width() // 2
        cy = int(pw.height() * 0.2)
        self.move(cx, cy)
        self.show()
        self.raise_()

        # Fade-out animation using windowOpacity on parent isn't ideal for overlays;
        # we use a QTimer to hide/delete after 3 s.
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._dismiss)
        self._timer.start(3000)

        # Opacity fade-out animation
        self._opacity_anim = QVariantAnimation(self)
        self._opacity_anim.setStartValue(1.0)
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.setDuration(400)
        self._opacity_anim.setEasingCurve(QEasingCurve.InQuad)
        self._opacity_anim.valueChanged.connect(self._on_opacity)
        # Start fade at 2600 ms (so it finishes at 3000 ms)
        QTimer.singleShot(2600, self._opacity_anim.start)

    def _on_opacity(self, value: float) -> None:
        effect = self.graphicsEffect()
        if effect is None:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
        effect.setOpacity(value)

    def _dismiss(self) -> None:
        self.hide()
        self.deleteLater()

    @staticmethod
    def show_error(parent_window: QWidget, message: str) -> "QuickReplaceToast":
        """Convenience constructor — creates, shows, auto-dismisses the toast."""
        return QuickReplaceToast(parent_window, message)


class ExpandOverlay(QFrame):
    """
    Animated overlay frame that expands a text edit to cover the container window
    and shrinks back when the shrink button is pressed.
    """
    def __init__(
        self,
        target_edit: QTextEdit,
        parent_container: QWidget,
        title_text: str,
        start_widget: QWidget,
    ) -> None:
        super().__init__(parent_container)
        self.setObjectName("ExpandOverlayFrame")
        self.setStyleSheet("""
            QFrame#ExpandOverlayFrame {
                background-color: #ffffff;
                border: 2px solid #d0d0d0;
                border-radius: 20px;
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.95);
                color: #0a1a0a;
                border: 2px solid #0a0a0a;
                border-radius: 18px;
                padding: 12px 14px;
                font-size: 13px;
                selection-background-color: #4caf84;
                selection-color: #ffffff;
                font-family: 'Comfortaa';
            }
        """)
        self._target_edit = target_edit
        self._parent_container = parent_container
        self._start_widget = start_widget
        self._anim: QPropertyAnimation | None = None
        self._start_rect: QRect = QRect()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel(title_text)
        lbl.setStyleSheet("color: #0a0a0a; font-size: 20px; font-weight: 700; letter-spacing: 0.5px;"
                              " font-family: 'Playwrite US Modern', 'Comfortaa', sans-serif;")
        hdr.addWidget(lbl)
        hdr.addStretch(1)

        norm_shrink = _svg_icon("shrink", "#1b5e20", 16)
        hov_shrink = _svg_icon("shrink", "#000000", 16)
        self.shrink_btn = HoverIconButton(norm_shrink, hov_shrink)
        self.shrink_btn.setFixedSize(30, 30)
        self.shrink_btn.setToolTip("Shrink view")
        self.shrink_btn.setObjectName("MinimizeButton")
        self.shrink_btn.clicked.connect(self.animate_shrink)
        hdr.addWidget(self.shrink_btn)
        layout.addLayout(hdr)

        self._cloned_edit = QTextEdit()
        self._cloned_edit.setPlainText(target_edit.toPlainText())
        self._cloned_edit.setReadOnly(target_edit.isReadOnly())
        self._cloned_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cloned_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cloned_edit.setStyleSheet(target_edit.styleSheet())
        layout.addWidget(self._cloned_edit, 1)

        self._updating = False
        if not target_edit.isReadOnly():
            self._cloned_edit.textChanged.connect(self._sync_to_target)
            target_edit.textChanged.connect(self._sync_from_target)

    def _sync_to_target(self) -> None:
        if self._updating: return
        self._updating = True
        self._target_edit.setPlainText(self._cloned_edit.toPlainText())
        self._updating = False

    def _sync_from_target(self) -> None:
        if self._updating: return
        self._updating = True
        self._cloned_edit.setPlainText(self._target_edit.toPlainText())
        self._updating = False

    def animate_expand(self) -> None:
        start_pt = self._start_widget.mapTo(self._parent_container, QPoint(0, 0))
        self._start_rect = QRect(start_pt, self._start_widget.size())
        end_rect = self._parent_container.rect().adjusted(14, 14, -14, -14)

        self.setGeometry(self._start_rect)
        self.show()
        self.raise_()

        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setStartValue(self._start_rect)
        self._anim.setEndValue(end_rect)
        self._anim.start()

    def animate_shrink(self) -> None:
        if self._anim and self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()

        self._anim = QPropertyAnimation(self, b"geometry", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(self._start_rect)
        self._anim.finished.connect(self.close)
        self._anim.start()


def _get_active_icon(colored: bool, size: int = 18) -> QIcon:
    """Load active.png (colored) or not_active.png (inactive) as a QIcon."""
    asset = "active.png" if colored else "not_active.png"
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", asset))

    # Fallback: if asset missing, fall back to the other one or SVG
    if not os.path.exists(path):
        fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "active.png"))
        if os.path.exists(fallback):
            path = fallback
        else:
            return _svg_icon("check", "#1b5e20" if colored else "#aaaaaa", size)

    pixmap = QPixmap(path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    icon = QIcon()
    # Register for all modes so Qt never auto-greys or transforms the image
    for mode in (QIcon.Normal, QIcon.Disabled, QIcon.Active, QIcon.Selected):
        for state in (QIcon.On, QIcon.Off):
            icon.addPixmap(pixmap, mode, state)
    return icon


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
        self._saved_name: str | None = None
        self._saved_prompt: str | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        left_card = QFrame(); left_card.setObjectName("SettingsCard")
        left_card.setFixedWidth(145)
        ll = QVBoxLayout(left_card); ll.setContentsMargins(10, 10, 10, 10); ll.setSpacing(8)
        self._list = QListWidget(); self._list.setObjectName("TagList")
        self._list.setWordWrap(True)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        ll.addWidget(self._list, 1)

        left_vbox = QVBoxLayout(); left_vbox.setSpacing(12); left_vbox.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("Your Tags"); lbl.setObjectName("SectionHeader"); lbl.setAlignment(Qt.AlignCenter)
        left_vbox.addWidget(lbl)
        left_vbox.addWidget(left_card)
        nb = QPushButton("+ New Tag"); nb.setObjectName("Secondary"); nb.setFixedHeight(34)
        nb.clicked.connect(self._on_new)
        left_vbox.addWidget(nb)
        layout.addLayout(left_vbox)

        right_card = QFrame(); right_card.setObjectName("SingleWhiteCard")
        rl = QVBoxLayout(right_card); rl.setContentsMargins(16, 16, 16, 16); rl.setSpacing(10)

        name_row = QHBoxLayout()
        name_row.setSpacing(4)
        nl = QLabel("Tag Name")
        nl.setObjectName("SectionLabel")
        self._name_dot = QLabel("•")
        self._name_dot.setStyleSheet("color: #1b5e20; font-size: 14px;")
        self._name_dot.setAlignment(Qt.AlignCenter)
        self._name_dot.hide()
        name_row.addWidget(nl)
        name_row.addWidget(self._name_dot)
        name_row.addStretch(1)
        rl.addLayout(name_row)
        self._name_edit = QLineEdit(); self._name_edit.setPlaceholderText("e.g. LinkedIn Post, Professional Email…")
        self._name_edit.textChanged.connect(self._check_dirty)
        rl.addWidget(self._name_edit)

        inst_row = QHBoxLayout()
        inst_row.setSpacing(4)
        pl = QLabel("Instructions")
        pl.setObjectName("SectionLabel")
        self._prompt_dot = QLabel("•")
        self._prompt_dot.setStyleSheet("color: #1b5e20; font-size: 14px;")
        self._prompt_dot.setAlignment(Qt.AlignCenter)
        self._prompt_dot.hide()
        inst_row.addWidget(pl)
        inst_row.addWidget(self._prompt_dot)
        inst_row.addStretch(1)
        rl.addLayout(inst_row)

        vt = QHBoxLayout(); vt.setSpacing(8)
        self._raw_btn = QPushButton("Raw"); self._raw_btn.setObjectName("ViewToggle")
        self._raw_btn.setCheckable(True); self._raw_btn.setChecked(True)
        self._raw_btn.clicked.connect(self._show_raw); vt.addWidget(self._raw_btn)
        self._md_btn = QPushButton("Markdown"); self._md_btn.setObjectName("ViewToggle")
        self._md_btn.setCheckable(True)
        self._md_btn.clicked.connect(self._show_md); vt.addWidget(self._md_btn)
        vt.addStretch(1)

        norm_exp = _svg_icon("expand", "#1b5e20", 16)
        hov_exp = _svg_icon("expand", "#000000", 16)
        self._prompt_expand_btn = HoverIconButton(norm_exp, hov_exp)
        self._prompt_expand_btn.setObjectName("IconButton")
        self._prompt_expand_btn.setFixedSize(30, 30)
        self._prompt_expand_btn.setToolTip("Expand prompt instructions view")
        self._prompt_expand_btn.clicked.connect(self._on_expand_prompt)
        vt.addWidget(self._prompt_expand_btn)
        rl.addLayout(vt)

        sub = QLabel("Define how selected text should be transformed:"); sub.setObjectName("SubLabel")
        sub.setWordWrap(True); rl.addWidget(sub)

        self._stack = QStackedWidget()
        self._prompt_edit = QTextEdit()
        self._prompt_edit.setPlaceholderText("Describe the desired style, tone and format… (Markdown supported)")
        self._prompt_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._prompt_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._prompt_edit.textChanged.connect(self._sync_preview)
        self._prompt_edit.textChanged.connect(self._check_dirty)
        self._stack.addWidget(self._prompt_edit)
        self._preview = QTextEdit(); self._preview.setReadOnly(True)
        self._preview.setPlaceholderText("Markdown preview…")
        self._preview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._preview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._stack.addWidget(self._preview)
        rl.addWidget(self._stack, 1)

        br = QHBoxLayout(); br.setSpacing(12)
        self._del_btn = QPushButton("Delete"); self._del_btn.setObjectName("Danger")
        self._del_btn.setFixedHeight(38); self._del_btn.setMinimumWidth(90)
        self._del_btn.clicked.connect(self._on_delete); br.addWidget(self._del_btn)
        br.addStretch(1)
        self._save_btn = QPushButton("Save Tag"); self._save_btn.setObjectName("Primary")
        self._save_btn.setFixedHeight(38); self._save_btn.setMinimumWidth(110)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._on_save); br.addWidget(self._save_btn)
        rl.addLayout(br)
        layout.addWidget(right_card, 1)

        self._list.currentTextChanged.connect(self._on_select)
        self.reload()

    def _on_expand_prompt(self) -> None:
        overlay = ExpandOverlay(
            target_edit=self._prompt_edit,
            parent_container=self.window(),
            title_text="Instructions  •  Expanded View",
            start_widget=self._prompt_edit,
        )
        overlay.animate_expand()

    def _check_dirty(self) -> None:
        curr_n = self._name_edit.text().strip()
        curr_p = self._prompt_edit.toPlainText().strip()
        orig_n = (self._saved_name or "").strip()
        orig_p = (self._saved_prompt or "").strip()

        name_dirty = curr_n != orig_n
        prompt_dirty = curr_p != orig_p

        self._name_dot.setVisible(name_dirty)
        self._prompt_dot.setVisible(prompt_dirty)

        dirty = name_dirty or prompt_dirty
        self._save_btn.setEnabled(dirty and bool(curr_n) and bool(curr_p))

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
        self._current_name = n
        self._name_edit.blockSignals(True)
        self._prompt_edit.blockSignals(True)
        self._name_edit.setText(n)
        p = self._store.prompt_for(n)
        self._prompt_edit.setPlainText(p); self._preview.setMarkdown(p)
        self._saved_name = n
        self._saved_prompt = p
        self._name_edit.blockSignals(False)
        self._prompt_edit.blockSignals(False)
        self._check_dirty()
        self._del_btn.setEnabled(True)

    def _on_new(self):
        self._list.clearSelection(); self._list.setCurrentRow(-1)
        self._current_name = None
        self._name_edit.blockSignals(True)
        self._prompt_edit.blockSignals(True)
        self._name_edit.clear()
        self._prompt_edit.clear(); self._preview.clear()
        self._saved_name = ""
        self._saved_prompt = ""
        self._name_edit.blockSignals(False)
        self._prompt_edit.blockSignals(False)
        self._check_dirty()
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
        self._saved_name = name
        self._saved_prompt = prompt
        self._save_btn.setEnabled(False)
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

        # --- Toggle Options (using the AI Model style) ---
        # Always on Top
        self._top_toggle = self._create_toggle_option(
            label="Keep the floating window always on top",
            config_key="always_on_top",
            default=True,
            description="Ensures the BetterIt window stays above all other applications, so you don't have to keep refocusing it."
        )
        cl.addWidget(self._top_toggle)

        # Quick Replace
        self._qr_toggle = self._create_toggle_option(
            label="Quick Replace",
            config_key="quick_replace",
            default=False,
            description="When enabled, select any text and press Ctrl+Space — BetterIt will silently polish it and instantly replace the selection in-place, without opening any window."
        )
        cl.addWidget(self._qr_toggle)

        hk = QWidget()
        hkl = QVBoxLayout(hk); hkl.setContentsMargins(0, 12, 0, 12); hkl.setSpacing(6)
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

    def _create_toggle_option(self, label: str, config_key: str, default: bool, description: str) -> QWidget:
        """Creates a toggle option with an active/inactive icon, removing the boxed border."""
        frame = QWidget()
        layout = QVBoxLayout(frame); layout.setContentsMargins(0, 4, 0, 12); layout.setSpacing(6)

        trigger_row = QHBoxLayout(); trigger_row.setSpacing(10)

        # Active/Inactive button
        current_val = bool(self._store.get_config(config_key, default))
        btn = QPushButton()
        btn.setFixedSize(26, 26)
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(_get_active_icon(current_val, 20))
        btn.setIconSize(QSize(20, 20))
        btn.setStyleSheet("QPushButton { background: transparent; border: none; }")

        # Option label
        lbl = QLabel(label); lbl.setObjectName("SectionLabel")
        lbl.setStyleSheet("color: #0a2e0a; font-size: 13px; font-weight: 700; text-transform: none; letter-spacing: 0px;")

        trigger_row.addWidget(btn)
        trigger_row.addWidget(lbl)
        trigger_row.addStretch(1)

        # Description label - plain text, no box
        desc = QLabel(description); desc.setObjectName("SubLabel")
        desc.setWordWrap(True)
        # Removed setContentsMargins to prevent text from being cut off or misaligned

        layout.addLayout(trigger_row)
        layout.addWidget(desc)

        def toggle():
            new_val = not bool(self._store.get_config(config_key, default))
            self._store.set_config(config_key, new_val)
            btn.setIcon(_get_active_icon(new_val, 20))

        btn.clicked.connect(toggle)
        return frame

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
    finished = Signal(str, bool, str)  # model_id, success, message

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__()
        self._api_key = api_key
        self._model = model

    @Slot()
    def run(self) -> None:
        success, message = test_reachability(api_key=self._api_key, model=self._model)
        self.finished.emit(self._model, success, message)


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
        self._is_active = is_active
        self._space_data = space_data
        self._space_name = str(space_data.get("name", "OpenRouter"))
        self._store = tag_store

        # Parallel Concurrency
        self._test_threads: dict[str, QThread] = {}
        self._test_workers: dict[str, ReachabilityWorker] = {}
        self._active_test_models: set[str] = set()

        # Live references to model rows + buttons + result labels
        self._model_row_frames: dict[str, QFrame] = {}
        self._test_btns: dict[str, QPushButton] = {}
        self._model_result_labels: dict[str, QLabel] = {}

        # Loading animation
        self._loading_timer = QTimer(self)
        self._loading_timer.setInterval(380)
        self._loading_dot_idx = 0
        self._loading_timer.timeout.connect(self._animate_loading)

        self._key_revealed = False

        # Animation tracking
        self._row_anims: dict[str, QPropertyAnimation] = {}        # row height slide
        self._test_opacity_effects: dict[str, QGraphicsOpacityEffect] = {}  # test btn fade
        self._row_color_anims: dict[str, QVariantAnimation] = {}   # row bg color tween

        # Card border: green if active, dark if not; alpha background matching settings cards
        self.setObjectName("KeyProfileCard")
        self.setStyleSheet(
            "QFrame#KeyProfileCard{background:rgba(255,255,255,0.70);border:2.5px solid #1b5e20;border-radius:20px;}"
            if is_active else
            "QFrame#KeyProfileCard{background:rgba(255,255,255,0.70);border:2px solid #0a0a0a;border-radius:20px;}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        # ── Header ──────────────────────────────────────────────────────
        hdr = QHBoxLayout(); hdr.setSpacing(8)

        name_lbl = QLabel(self._space_name); name_lbl.setObjectName("CardTitle")
        hdr.addWidget(name_lbl)

        if is_active:
            badge = QLabel("Active Space"); badge.setObjectName("ActiveBadge")
            hdr.addWidget(badge)

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
        api_lbl_row.addWidget(QLabel("API Key", objectName="PaneLabel"), 1)
        root.addLayout(api_lbl_row)

        stored_key: str = str(self._space_data.get("api_key", "") or "")

        key_row = QHBoxLayout(); key_row.setSpacing(8)
        self._key_edit = QLineEdit()
        self._key_edit.setFixedHeight(38)
        self._key_edit.setStyleSheet(
            "QLineEdit { border: 1px solid rgba(10,10,10,0.18); border-radius: 16px; "
            "background: rgba(255,255,255,0.85); color: #0a1a0a; padding: 8px 14px; "
            "font-size: 13px; font-family: 'Comfortaa'; } "
            "QLineEdit:focus { border: 1.5px solid rgba(27,94,32,0.45); background:#fff; }"
        )

        if stored_key:
            # Show masked: first 3 + dots + last 3
            masked = self._mask_key(stored_key)
            self._key_edit.setText(masked)
            self._key_edit.setReadOnly(True)
            self._key_edit.setPlaceholderText("")
        else:
            self._key_edit.setText("")
            self._key_edit.setReadOnly(False)
            self._key_edit.setPlaceholderText("sk-or-v1-…  Paste your API key here")

        # Auto-save when user finishes typing a new key
        self._key_edit.editingFinished.connect(self._commit_key)

        key_row.addWidget(self._key_edit, 1)
        root.addLayout(key_row)

        # ── Models list ──────────────────────────────────────────────────
        ml_row = QHBoxLayout(); ml_row.setSpacing(6)
        ml_row.addWidget(QLabel("Configured Models", objectName="PaneLabel"), 1)
        root.addLayout(ml_row)

        models = list(self._space_data.get("models", []))
        selected = str(self._space_data.get("selected_model", models[0] if models else ""))

        self._models_container = QVBoxLayout(); self._models_container.setSpacing(5)
        for m in models:
            is_row_active = self._is_active and (m == selected)
            self._build_model_row(m, is_row_active, len(models))
        root.addLayout(self._models_container)

        # ── Add Model ────────────────────────────────────────────────────
        add_row = QHBoxLayout(); add_row.setSpacing(8)
        self._add_edit = QLineEdit()
        self._add_edit.setFixedHeight(34)
        self._add_edit.setPlaceholderText("Model ID  (e.g. google/gemini-2.5-pro, deepseek/deepseek-r1)")
        self._add_edit.setStyleSheet(
            "QLineEdit { border: 1px solid rgba(10,10,10,0.18); border-radius: 14px; "
            "background: rgba(255,255,255,0.85); color: #0a1a0a; padding: 4px 12px; font-size: 12px; font-family: 'Comfortaa'; } "
            "QLineEdit:focus { border: 1.5px solid rgba(27,94,32,0.45); background: #ffffff; }"
        )
        self._add_edit.returnPressed.connect(self._add_model)
        add_row.addWidget(self._add_edit, 1)

        add_btn = QPushButton("Add Model"); add_btn.setObjectName("Secondary")
        add_btn.setFixedHeight(34)
        add_btn.setStyleSheet(
            "QPushButton { border: 1px solid rgba(10,10,10,0.18); border-radius: 14px; "
            "background: rgba(255,255,255,0.85); color: #1b5e20; font-weight: 700; font-size: 12px; padding: 4px 12px; } "
            "QPushButton:hover { border: 1.5px solid rgba(27,94,32,0.45); background: rgba(237,250,237,0.95); }"
        )
        add_btn.setIcon(_svg_icon("add_folder", "#1b5e20", 14)); add_btn.setIconSize(QSize(14, 14))
        add_btn.clicked.connect(self._add_model)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)

    # ── model row factory ─────────────────────────────────────────────────

    def _build_model_row(self, model_id: str, is_sel: bool, total: int) -> None:
        row = QFrame(); row.setObjectName("ModelRowFrame")
        # Translucent alpha row styling matching window UI
        row.setStyleSheet(
            "QFrame{background:rgba(237,250,237,0.85);border:none;border-radius:13px;}"
            if is_sel else
            "QFrame{background:rgba(255,255,255,0.55);border:none;border-radius:13px;}")
        self._model_row_frames[model_id] = row

        # Main row layout is vertical to stack row contents and test result label
        main_layout = QVBoxLayout(row)
        main_layout.setContentsMargins(10, 6, 10, 6)
        main_layout.setSpacing(4)

        # Top row for controls
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        lbl = QLabel(model_id); lbl.setObjectName("ModelNameLabel")
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_row.addWidget(lbl, 1)

        # 1. Active Selection Button (26x26, flat, icon-only — NO border, NO background ever)
        active_btn = QPushButton()
        active_btn.setFixedSize(26, 26)
        active_btn.setIconSize(QSize(20, 20))
        active_btn.setFlat(True)           # removes the platform-drawn frame
        active_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                outline: none;
                padding: 0px;
            }
            QPushButton:hover {
                background: transparent;
                border: none;
            }
            QPushButton:pressed {
                background: transparent;
                border: none;
            }
            QPushButton:focus {
                background: transparent;
                border: none;
                outline: none;
            }
        """)
        if is_sel:
            active_btn.setIcon(_get_active_icon(True, 20))
            active_btn.setToolTip("Active (current)")
            # No click handler — already active
        else:
            active_btn.setIcon(_get_active_icon(False, 20))
            active_btn.setToolTip("Set Active")
            active_btn.clicked.connect(lambda _, m=model_id: self._set_active_model(m))
        top_row.addWidget(active_btn)

        # 2. Test Button (26x26, flat, invisible/empty until hovered)
        test_btn = QPushButton()
        test_btn.setObjectName("ModelTestBtn")
        test_btn.setFixedSize(26, 26)
        test_btn.setIconSize(QSize(20, 20))
        test_btn.setFlat(True)
        test_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; outline: none; padding: 0px; }
            QPushButton:hover { background: transparent; border: none; }
            QPushButton:pressed { background: transparent; border: none; }
            QPushButton:focus { background: transparent; border: none; outline: none; }
        """)
        test_btn.setIcon(QIcon())
        test_btn.setToolTip("")
        test_btn.clicked.connect(lambda _, m=model_id: self._run_test(m))
        top_row.addWidget(test_btn)
        self._test_btns[model_id] = test_btn

        # 3. Delete Button (26x26, flat, delete.png icon)
        del_btn = QPushButton()
        del_btn.setObjectName("DangerIcon")
        del_btn.setFixedSize(26, 26)
        del_btn.setIconSize(QSize(20, 20))
        del_btn.setFlat(True)
        del_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; outline: none; padding: 0px; }
            QPushButton:hover { background: transparent; border: none; }
            QPushButton:pressed { background: transparent; border: none; }
            QPushButton:focus { background: transparent; border: none; outline: none; }
        """)
        del_btn.setIcon(_svg_icon("trash", "#c0392b", 20))
        del_btn.setEnabled(total > 1)
        del_btn.setToolTip("Remove model")
        del_btn.clicked.connect(lambda _, m=model_id: self._del_model(m))
        top_row.addWidget(del_btn)

        # ── Opacity effect on test button (fades in on hover, fades out on leave) ──
        test_opacity = QGraphicsOpacityEffect(test_btn)
        test_opacity.setOpacity(0.0)
        test_btn.setGraphicsEffect(test_opacity)
        self._test_opacity_effects[model_id] = test_opacity

        main_layout.addLayout(top_row)

        # ── Result label: starts collapsed (maxHeight=0), expands via animation ──
        res_lbl = QLabel("")
        res_lbl.setWordWrap(True)
        res_lbl.setStyleSheet(
            "border: none; background: transparent; font-size: 11px; "
            "font-family: 'Comfortaa'; padding-top: 2px; padding-left: 2px;"
        )
        res_lbl.setMaximumHeight(0)    # collapsed by default — no hide(), uses layout height
        main_layout.addWidget(res_lbl)
        self._model_result_labels[model_id] = res_lbl

        # Connect mouse hover events to the row container
        row.enterEvent = lambda event, m=model_id: self._on_row_hover(m, True)
        row.leaveEvent = lambda event, m=model_id: self._on_row_hover(m, False)

        self._models_container.addWidget(row)

    # ── helpers ───────────────────────────────────────────────────────────

    def _animate_opacity(self, model_id: str, to_opacity: float, duration: int = 160) -> None:
        """Smoothly fade the test button's opacity effect to `to_opacity`."""
        eff = self._test_opacity_effects.get(model_id)
        if not eff:
            return
        anim = QVariantAnimation(self)
        anim.setStartValue(eff.opacity())
        anim.setEndValue(to_opacity)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(lambda v, e=eff: e.setOpacity(float(v)))
        anim.start(QVariantAnimation.DeleteWhenStopped)

    def _animate_result_label(self, model_id: str, expand: bool) -> None:
        """Slide the result label open (expand=True) or shut (expand=False)."""
        lbl = self._model_result_labels.get(model_id)
        if not lbl:
            return
        lbl.setMaximumHeight(16777215)          # unlock so sizeHint is computed
        target_h = lbl.sizeHint().height() + 6 if expand else 0
        lbl.setMaximumHeight(lbl.height())      # re-lock at current height for smooth start

        anim = self._row_anims.get(model_id)
        if anim:
            try:
                if anim.state() == QPropertyAnimation.Running:
                    anim.stop()
            except RuntimeError:
                pass

        anim = QPropertyAnimation(lbl, b"maximumHeight", self)
        anim.setDuration(220)
        anim.setStartValue(lbl.maximumHeight())
        anim.setEndValue(target_h)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self._row_anims[model_id] = anim
        anim.start()

    def _on_row_hover(self, model_id: str, hover: bool) -> None:
        """Fade-in or fade-out the test (play) button icon on row hover."""
        if model_id in self._active_test_models:
            return
        btn = self._test_btns.get(model_id)
        if btn:
            if hover:
                btn.setIcon(_svg_icon("play", "#1b5e20", 20))
                btn.setToolTip("Test Connection")
                self._animate_opacity(model_id, 1.0, 160)
            else:
                self._animate_opacity(model_id, 0.0, 200)
                # Clear the icon after fade completes
                QTimer.singleShot(210, lambda b=btn: b.setIcon(QIcon()) if not b.underMouse() else None)
                btn.setToolTip("")

    @staticmethod
    def _mask_key(key: str) -> str:
        """Show first 3 + '•••••' + last 3 chars of an API key."""
        if len(key) <= 8:
            return "•" * len(key)
        return key[:3] + "  •••••••  " + key[-3:]

    def _commit_key(self) -> None:
        """Called on editingFinished — save the new raw key and switch back to masked display."""
        if self._key_edit.isReadOnly():
            return          # masked display mode, nothing to commit
        raw = self._key_edit.text().strip()
        if raw:
            self._store.update_key_space(self._space_name, api_key=raw)
            # Switch back to masked read-only display
            self._key_edit.setText(self._mask_key(raw))
            self._key_edit.setReadOnly(True)

    def _save_key(self) -> None:
        """Legacy stub — kept so existing signals don't break."""
        self._commit_key()

    def _set_active_model(self, model_id: str) -> None:
        self._store.set_active_key_space_name(self._space_name)
        self._store.update_key_space(self._space_name, selected_model=model_id)
        self.profile_changed.emit()

    def _del_model(self, model_id: str) -> None:
        if self._store.delete_model_from_space(self._space_name, model_id):
            self.profile_changed.emit()

    def _add_model(self) -> None:
        mid = self._add_edit.text().strip()
        if not mid:
            show_themed_warning(self, "Missing Model ID", "Please enter a model ID first.")
            return
        self._store.add_model_to_space(self._space_name, mid)
        self._add_edit.clear(); self.profile_changed.emit()

    # ── test flow ─────────────────────────────────────────────────────────

    def _animate_loading(self) -> None:
        """Cycle dots inside the row's inline result label while testing is in progress."""
        frames = ["", ".", "..", "..."]
        self._loading_dot_idx = (self._loading_dot_idx + 1) % len(frames)
        for mid in list(self._active_test_models):
            lbl = self._model_result_labels.get(mid)
            if lbl:
                lbl.setStyleSheet("color: #1b5e20; border: none; background: transparent;")
                lbl.setText(f"Connecting ({mid}){frames[self._loading_dot_idx]}")
                self._animate_result_label(mid, True)

    def _run_test(self, model_id: str) -> None:
        if model_id in self._active_test_models:
            return

        # Fetch the real raw API key (not the UI masked display string)
        space = self._store.get_key_space(self._space_name) or self._space_data
        api_key = str(space.get("api_key", "") or "").strip()
        if not api_key or "•" in api_key:
            txt = self._key_edit.text().strip()
            if txt and "•" not in txt:
                api_key = txt

        if not api_key or "•" in api_key:
            # Show a temporary inline warning directly in the row result
            lbl = self._model_result_labels.get(model_id)
            if lbl:
                lbl.setStyleSheet("color: #c0392b; font-weight: 700; border: none; background: transparent;")
                lbl.setText("Error: Enter a valid API key first.")
                self._animate_result_label(model_id, True)
                QTimer.singleShot(3000, lambda m=model_id: self._collapse_result(m))
            return

        # Lock test button opacity to 1 (visible) while testing
        eff = self._test_opacity_effects.get(model_id)
        if eff:
            eff.setOpacity(1.0)

        # Animate the Test button → loading spinner
        btn = self._test_btns.get(model_id)
        if btn:
            btn.setEnabled(False)
            btn.setIcon(_svg_icon("loading", "#1b5e20", 20))
            btn.setToolTip("Testing…")

        # Grey the row while in-flight
        row = self._model_row_frames.get(model_id)
        if row:
            row.setStyleSheet(
                "QFrame{background:rgba(245,245,245,0.85);border:none;border-radius:13px;}")

        self._active_test_models.add(model_id)
        if not self._loading_timer.isActive():
            self._loading_dot_idx = 0
            self._loading_timer.start()

        thread = QThread(self)
        worker = ReachabilityWorker(api_key, model_id)
        worker.moveToThread(thread)

        self._test_threads[model_id] = thread
        self._test_workers[model_id] = worker

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_result, Qt.QueuedConnection)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        def _cleanup(mid=model_id):
            self._test_threads.pop(mid, None)
            self._test_workers.pop(mid, None)

        thread.finished.connect(_cleanup)
        thread.start()

    @Slot(str, bool, str)
    def _on_result(self, model_id: str, success: bool, message: str) -> None:
        self._active_test_models.discard(model_id)
        if not self._active_test_models:
            self._loading_timer.stop()

        # Restore Test button
        btn = self._test_btns.get(model_id)
        if btn:
            btn.setEnabled(True)
            row = self._model_row_frames.get(model_id)
            if row and row.underMouse():
                btn.setIcon(_svg_icon("play", "#1b5e20", 20))
                btn.setToolTip("Test Connection")
                self._animate_opacity(model_id, 1.0, 120)
            else:
                btn.setIcon(QIcon())
                btn.setToolTip("")
                self._animate_opacity(model_id, 0.0, 250)

        # Colour the model row green or red (instant border, fades in via label)
        row = self._model_row_frames.get(model_id)
        if row:
            if success:
                row.setStyleSheet(
                    "QFrame{background:rgba(212,248,212,0.90);border:none;border-radius:13px;}")
            else:
                row.setStyleSheet(
                    "QFrame{background:rgba(253,216,216,0.90);border:none;border-radius:13px;}")

        # Slide open the result label
        res_lbl = self._model_result_labels.get(model_id)
        if res_lbl:
            if success:
                res_lbl.setStyleSheet("color: #1b5e20; font-weight: 700; border: none; background: transparent;")
                res_lbl.setText(f"✓  {message}")
            else:
                res_lbl.setStyleSheet("color: #c0392b; font-weight: 700; border: none; background: transparent;")
                res_lbl.setText(f"✗  {message}")
            self._animate_result_label(model_id, True)

            # Schedule auto-collapse after 3 seconds
            QTimer.singleShot(3000, lambda m=model_id: self._collapse_result(m))

    def _collapse_result(self, model_id: str | None) -> None:
        """Animate the result label closed and restore row color."""
        if not model_id:
            return
        self._animate_result_label(model_id, False)

        row = self._model_row_frames.get(model_id)
        if row:
            models = list(self._space_data.get("models", []))
            selected = str(self._space_data.get("selected_model", models[0] if models else ""))
            is_active = (model_id == selected)
            if is_active:
                row.setStyleSheet(
                    "QFrame{background:rgba(237,250,237,0.85);border:none;border-radius:13px;}")
            else:
                row.setStyleSheet(
                    "QFrame{background:rgba(255,255,255,0.55);border:none;border-radius:13px;}")


# ---------------------------------------------------------------------------
# Inline New-Profile Card  (no popups)
# ---------------------------------------------------------------------------

class NewProfileCardWidget(QFrame):
    created = Signal(str)

    def __init__(self, tag_store: TagStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = tag_store
        self._is_expanded = False
        self.setObjectName("NewProfileCard")
        self.setStyleSheet(
            "QFrame#NewProfileCard{background:rgba(255,255,255,0.70);border:2px solid #0a0a0a;border-radius:20px;}"
        )

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
        create.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: #000000;
                font-weight: 700;
                font-family: 'Comfortaa';
                font-size: 13px;
                border: 2px solid #0a0a0a;
                border-radius: 17px;
                padding: 4px 18px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
                color: #ffffff;
            }
        """)
        create.setFixedHeight(34)
        create.clicked.connect(self._create); br.addWidget(create)
        fl.addLayout(br)

        self._layout.addWidget(self._form)
        self._form.setMaximumHeight(0)   # collapsed by default

        self._form_anim: QPropertyAnimation | None = None

    def _animate_form(self, expand: bool) -> None:
        """Slide the form in (expand=True) or out (expand=False) by animating maximumHeight."""
        self._form.setMaximumHeight(16777215)
        target = self._form.sizeHint().height() + 12 if expand else 0
        self._form.setMaximumHeight(self._form.height())

        if self._form_anim:
            try:
                if self._form_anim.state() == QPropertyAnimation.Running:
                    self._form_anim.stop()
            except RuntimeError:
                pass

        self._form_anim = QPropertyAnimation(self._form, b"maximumHeight", self)
        self._form_anim.setDuration(260)
        self._form_anim.setStartValue(self._form.maximumHeight())
        self._form_anim.setEndValue(target)
        self._form_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._form_anim.start()

    def _expand(self) -> None:
        self._is_expanded = True
        self._open_btn.hide()
        self._name_edit.clear(); self._key_edit.clear(); self._err_lbl.setText("")
        self._form.setMaximumHeight(0)   # reset before animating open
        self._animate_form(True)
        QTimer.singleShot(50, self._name_edit.setFocus)

    def _collapse(self) -> None:
        self._is_expanded = False
        self._animate_form(False)
        QTimer.singleShot(270, lambda: self._open_btn.show())

    def _create(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            self._err_lbl.setStyleSheet("color:#c0392b;font-weight:700;font-family:'Comfortaa';font-size:11px;")
            self._err_lbl.setText("Please enter a profile name."); return
        if name.lower() in [s.lower() for s in self._store.get_key_space_names()]:
            self._err_lbl.setStyleSheet("color:#c0392b;font-weight:700;font-family:'Comfortaa';font-size:11px;")
            self._err_lbl.setText(f'Profile "{name}" already exists.'); return
        self._store.add_key_space(name, api_key=self._key_edit.text().strip())
        self._collapse()
        self.created.emit(name)


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

    def reload(self, animate_space: str | None = None) -> None:
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

            if animate_space and name == animate_space:
                eff = QGraphicsOpacityEffect(card)
                eff.setOpacity(0.0)
                card.setGraphicsEffect(eff)

                anim_o = QVariantAnimation(self)
                anim_o.setDuration(350)
                anim_o.setStartValue(0.0)
                anim_o.setEndValue(1.0)
                anim_o.setEasingCurve(QEasingCurve.OutCubic)
                anim_o.valueChanged.connect(lambda v, e=eff: e.setOpacity(float(v)))
                anim_o.start(QVariantAnimation.DeleteWhenStopped)

        new_card = NewProfileCardWidget(self._store)
        new_card.created.connect(lambda space_name="": self.reload(animate_space=space_name))
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
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

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
        pl.addLayout(ph)

        # Flow Image
        flow_img_path = get_resource_path("assets/flow_app.png")
        flow_lbl = QLabel()
        if os.path.exists(flow_img_path):
            pix = QPixmap(flow_img_path)
            scaled_pix = pix.scaledToWidth(500, Qt.SmoothTransformation)
            flow_lbl.setPixmap(scaled_pix)
        else:
            flow_lbl.setText("Flow image not found")
        flow_lbl.setAlignment(Qt.AlignCenter)
        pl.addWidget(flow_lbl)
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


# ---------------------------------------------------------------------------
# Quick Replace Loading Components
# ---------------------------------------------------------------------------

class PencilLoaderWidget(QWidget):
    """
    A specialized widget that shows a pencil icon with an optional rotating
    loading border and an expandable error state.
    """
    IDLE = 0
    LOADING = 1
    ERROR = 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(QSize(54, 54))
        self._locked = False

        self._state = self.IDLE
        self._error_msg: str | None = None
        self._angle = 0

        # Loading timer
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._advance_angle)

        # Load pencil image
        pencil_path = Path(__file__).resolve().parent.parent.parent / "assets" / "pencil.png"
        if pencil_path.exists():
            self._pencil_pixmap = QPixmap(str(pencil_path)).scaled(
                QSize(30, 30), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        else:
            self._pencil_pixmap = None

    def _advance_angle(self) -> None:
        self._angle = (self._angle + 12) % 360
        self.update()

    def set_loading(self, loading: bool) -> None:
        self._locked = loading
        if loading:
            self._state = self.LOADING
            self._timer.start()
        else:
            self._state = self.IDLE
            self._timer.stop()
        self.update()

    def set_error(self, message: str | None) -> None:
        if message:
            self._state = self.ERROR
            self._error_msg = message
            # Calculate a dynamic width based on text length to avoid clipping
            # Base width 240, plus some extra for longer messages, max 450
            estimated_width = max(240, min(450, len(message) * 8 + 80))
            self.setFixedSize(QSize(estimated_width, 54))
        else:
            self._state = self.IDLE
            self._error_msg = None
            self.setFixedSize(QSize(54, 54))
        self._timer.stop()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self._state == self.ERROR:
            # Draw Pill Shape
            rect = self.rect().adjusted(2, 2, -2, -2)
            painter.setBrush(QBrush(QColor("#1a1a1a")))
            painter.setPen(QPen(QColor("#444444"), 1.5))
            painter.drawRoundedRect(rect, 25, 25)

            # Draw Error Text
            if self._error_msg:
                text_rect = rect.adjusted(50, 0, -10, 0)
                painter.setPen(QPen(QColor("#ffffff")))
                font = painter.font()
                font.setFamily("Comfortaa")
                font.setPixelSize(12)
                painter.setFont(font)
                painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap, self._error_msg)

            # Draw small pencil icon on the left
            if self._pencil_pixmap:
                px = 12
                py = (self.height() - self._pencil_pixmap.height()) // 2
                painter.drawPixmap(px, py, self._pencil_pixmap)

        else:
            # Circular state (IDLE or LOADING)
            # Draw the pencil first
            if self._pencil_pixmap:
                px = (self.width() - self._pencil_pixmap.width()) // 2
                py = (self.height() - self._pencil_pixmap.height()) // 2
                painter.drawPixmap(px, py, self._pencil_pixmap)

            # Draw the loading border
            if self._state == self.LOADING:
                pen_track = QPen(QColor("#a8d5a8"), 3)
                painter.setPen(pen_track)
                painter.drawEllipse(4, 4, self.width() - 8, self.height() - 8)

                pen_arc = QPen(QColor("#1b5e20"), 4)
                painter.setPen(pen_arc)
                start = self._angle * 16
                span = 280 * 16 # Approx 280 degrees
                painter.drawArc(4, 4, self.width() - 8, self.height() - 8, start, span)

        painter.end()

# ---------------------------------------------------------------------------
# BallWidget (minimised floating ball)
# ---------------------------------------------------------------------------
class BallWidget(PencilLoaderWidget):
    expand_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._press_pos: QPoint | None = None
        self._dragging = False

    def show_at(self, pos: QPoint) -> None:
        self.move(pos); self.show(); self.raise_()

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
            if getattr(self, "_locked", False):
                return
            self.expand_requested.emit()
        self._drag_pos = self._press_pos = None; self._dragging = False
        super().mouseReleaseEvent(event)


class TransientPencilLoader(PencilLoaderWidget):
    """
    A transient loading indicator that appears at the bottom-center of the screen.
    """
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Set flags for top-level transient window
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show_at_bottom_center()

    def show_at_bottom_center(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 60
        self.move(x, y)
        self.show()
        self.raise_()


# ---------------------------------------------------------------------------
# Settings Window
# ---------------------------------------------------------------------------

class SettingsWindow(QDialog):
    tags_changed = Signal()
    minimize_requested = Signal()
    return_requested = Signal()

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

        self._return_btn = HoverIconButton(_svg_icon("return", "#000000", 16), _svg_icon("return", "#ffffff", 16))
        self._return_btn.setObjectName("MinimizeButton")
        self._return_btn.setFixedSize(30, 30)
        self._return_btn.setToolTip("Return to Better It")
        self._return_btn.clicked.connect(self._on_return_clicked)
        self._return_btn.hide()
        hdr.addWidget(self._return_btn)

        self._min_btn = QPushButton("–"); self._min_btn.setObjectName("MinimizeButton")
        self._min_btn.setFixedSize(30, 30); self._min_btn.setToolTip("Minimize to ball")
        self._min_btn.clicked.connect(self._on_minimize); hdr.addWidget(self._min_btn)

        self._close_btn = QPushButton("×"); self._close_btn.setObjectName("CloseButton")
        self._close_btn.setFixedSize(30, 30); self._close_btn.clicked.connect(self.close)
        hdr.addWidget(self._close_btn); root.addLayout(hdr)

        body = QHBoxLayout(); body.setSpacing(14)
        self._sidebar = QListWidget(); self._sidebar.setObjectName("Sidebar")
        self._sidebar.setFixedWidth(135)
        sidebar_font = QFont("Playwrite US Modern", 10, QFont.Bold)
        sidebar_font.setFamilies(["Playwrite US Modern", "Playwrite US Trad", "Playwrite US", "Playwrite", "Comfortaa", "sans-serif"])
        self._sidebar.setFont(sidebar_font)
        for label, _ in self.PAGES:
            item = QListWidgetItem(label)
            item.setFont(sidebar_font)
            self._sidebar.addItem(item)
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

    def set_return_visible(self, visible: bool) -> None:
        self._return_btn.setVisible(visible)

    def _on_return_clicked(self) -> None:
        self.hide()
        self.return_requested.emit()

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

    def set_ball_loading(self, loading: bool, error: str | None = None) -> None:
        """Proxy loading state to the minimized ball widget."""
        if self._ball:
            if error:
                self._ball.set_error(error)
            elif loading:
                self._ball.set_loading(True)
            else:
                self._ball.set_loading(False)

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
