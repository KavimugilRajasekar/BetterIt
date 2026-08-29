"""
The always-on-top floating window shown when the hotkey fires.
Drag & movable, fixed size, completely rounded corners,
green theme with slight transparency and clean layout.

The "Tag" selector sits in the same horizontal row as the "Polish" button.
Tapping "Polish" greys out the tag box (showing "Thinking…" instead of the
tag name) and swaps the "+" button for a loading spinner until the rewrite
comes back. Tapping "+" opens the bigger Settings window (settings.py),
which has a side panel with "Edit Tag" and "Settings" sections.
"""

from __future__ import annotations

import sys

from pathlib import Path

from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBitmap,
    QBrush,
    QColor,
    QFontDatabase,
    QIcon,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QRegion,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QStyle,
    QStyleOptionComboBox,
    QStylePainter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    # Normal case: window.py lives inside a package (e.g. aiwriter/window.py)
    # alongside settings.py, tag_store.py, and theme.py.
    from .settings import SettingsWindow, ExpandOverlay, _svg_icon
    from .tag_store import TagStore
    from .theme import STYLESHEET
except ImportError:
    # Fallback: window.py is being run/imported as a standalone script with
    # settings.py, tag_store.py, theme.py sitting next to it (no package).
    from settings import SettingsWindow, ExpandOverlay, _svg_icon
    from tag_store import TagStore
    from theme import STYLESHEET


# --- Window geometry ---------------------------------------------------------
# The fixed window must be tall enough to fit every row without squeezing/
# overlapping content (see _build_ui for the actual rows).
WINDOW_WIDTH = 460
WINDOW_HEIGHT = 500
CORNER_RADIUS = 26


# --- Custom widgets ---------------------------------------------------------

class Spinner(QWidget):
    """A tiny dependency-free rotating-arc spinner (green theme)."""

    def __init__(self, parent: QWidget | None = None, size: int = 20) -> None:
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(size, size)

    def start(self) -> None:
        self._angle = 0
        self._timer.start(50)
        self.update()

    def stop(self) -> None:
        self._timer.stop()

    def _advance(self) -> None:
        self._angle = (self._angle + 36) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Light green track
        pen = QPen(QColor("#a8d5a8"), 2.5)
        painter.setPen(pen)
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
        # Bright green arc
        pen = QPen(QColor("#1b5e20"), 3)
        painter.setPen(pen)
        start = self._angle * 16
        span = (360 - 80) * 16
        painter.drawArc(2, 2, self.width() - 4, self.height() - 4, start, span)


class MarqueeComboBox(QComboBox):
    """A QComboBox that horizontally scrolls ("floats") its current text
    when the selected tag name is too wide to fit in the shrunk box,
    instead of silently truncating it. The dropdown arrow still opens the
    normal list so another tag can always be picked."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._offset = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._advance)
        self.currentTextChanged.connect(self._sync_scroll_state)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_scroll_state()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_scroll_state()

    # -- measurement -------------------------------------------------------

    def _text_width(self) -> int:
        return self.fontMetrics().horizontalAdvance(self.currentText())

    def _text_rect(self):
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        rect = self.style().subControlRect(
            QStyle.CC_ComboBox, opt, QStyle.SC_ComboBoxEditField, self
        )
        rect.adjust(4, 0, -2, 0)
        return rect

    def _sync_scroll_state(self, *_args) -> None:
        if self._text_width() > self._text_rect().width():
            self._offset = 0.0
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
            self._offset = 0.0
        self.update()

    def _advance(self) -> None:
        self._offset += 1.5
        gap = 26
        total = self._text_width() + gap
        if self._offset >= total:
            self._offset = 0.0
        self.update()

    # -- painting ------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QStylePainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.currentText = ""  # we draw the text ourselves, below
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)

        rect = self._text_rect()
        text = self.currentText()
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(text)

        painter.save()
        painter.setClipRect(rect)
        painter.setPen(self.palette().buttonText().color() if self.isEnabled() else QColor("#6d8f6d"))
        y = rect.center().y() + (fm.ascent() - fm.descent()) // 2

        if text_w <= rect.width():
            painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, text)
        else:
            x = rect.x() - int(self._offset)
            painter.drawText(x, y, text)
            second_x = x + text_w + 26
            if second_x < rect.right():
                painter.drawText(second_x, y, text)
        painter.restore()


class HoverIconButton(QPushButton):
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


# --- Main window ------------------------------------------------------------

class FloatingWindow(QWidget):
    """
    The 'cutie' window: shows original text, runs grammar, shows replacement.
    Draggable, fixed size, green theme, fully rounded corners.
    """

    # Signals — the owning app connects these to the LLM worker / paste-back.
    correct_requested = Signal(str, str)  # emits (original text, tag prompt)
    replace_requested = Signal(str)       # emits the corrected text
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("FloatingWindow")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(QSize(WINDOW_WIDTH, WINDOW_HEIGHT))
        self.setMask(self._rounded_mask(WINDOW_WIDTH, WINDOW_HEIGHT, CORNER_RADIUS))

        self._tag_store = TagStore()
        self._settings_window: SettingsWindow | None = None

        # For dragging
        self._drag_pos: QPoint | None = None

        # Main container with rounded corners and transparency
        self._container = QWidget(self)
        self._container.setGeometry(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self._container.setObjectName("FloatingWindow")
        self._container.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._wire_signals()
        self._reset_to_idle()

        # Enable dragging from container
        self._container.mousePressEvent = self._mouse_press_event
        self._container.mouseMoveEvent = self._mouse_move_event

    def _rounded_mask(self, width: int, height: int, radius: int):
        """Return a raster mask matching the rounded window shell."""
        bitmap = QBitmap(width, height)
        bitmap.fill(Qt.color0)

        painter = QPainter(bitmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.color1)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, radius, radius)
        painter.end()

        return QRegion(bitmap)

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self._container)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        # Title row (draggable area)
        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        self._title = QLabel("Better It")
        self._title.setObjectName("Title")
        self._title.setStyleSheet("QLabel#Title { font-size: 24px; font-weight: 700; }")
        # Make title area draggable
        self._title.mousePressEvent = self._mouse_press_event
        self._title.mouseMoveEvent = self._mouse_move_event
        title_row.addWidget(self._title)
        title_row.addStretch(1)

        # Settings button (assets/settings_grey.png default, assets/settings.png on hover, no outer border, positioned just left of 'x')
        assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
        grey_path = assets_dir / "settings_grey.png"
        color_path = assets_dir / "settings.png"

        normal_icon = QIcon(str(grey_path)) if grey_path.exists() else QIcon()
        hover_icon = QIcon(str(color_path)) if color_path.exists() else normal_icon

        self._settings_btn = HoverIconButton(normal_icon, hover_icon)
        self._settings_btn.setObjectName("HeaderSettingsBtn")
        self._settings_btn.setToolTip("Manage tags & settings")
        self._settings_btn.setFixedSize(28, 28)
        self._settings_btn.setIconSize(QSize(22, 22))
        self._settings_btn.setFlat(True)
        self._settings_btn.setStyleSheet("""
            QPushButton#HeaderSettingsBtn {
                background: transparent;
                border: none;
                outline: none;
                padding: 0px;
            }
            QPushButton#HeaderSettingsBtn:hover {
                background: transparent;
                border: none;
            }
            QPushButton#HeaderSettingsBtn:pressed {
                background: transparent;
                border: none;
            }
        """)
        title_row.addWidget(self._settings_btn)

        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("CloseButton")
        self._close_btn.setFixedSize(30, 30)
        title_row.addWidget(self._close_btn)
        root.addLayout(title_row)

        # Original pane header
        orig_hdr = QHBoxLayout()
        self._original_label = self._make_pane_label("Original")
        orig_hdr.addWidget(self._original_label)
        orig_hdr.addStretch(1)

        norm_exp = _svg_icon("expand", "#1b5e20", 15)
        hov_exp = _svg_icon("expand", "#000000", 15)
        self._orig_expand_btn = HoverIconButton(norm_exp, hov_exp)
        self._orig_expand_btn.setFixedSize(24, 24)
        self._orig_expand_btn.setToolTip("Expand original text view")
        self._orig_expand_btn.setStyleSheet("background: transparent; border: none;")
        self._orig_expand_btn.clicked.connect(self._on_expand_original)
        orig_hdr.addWidget(self._orig_expand_btn)
        root.addLayout(orig_hdr)

        self._original = QTextEdit()
        self._original.setReadOnly(True)
        self._original.setFixedHeight(80)
        self._original.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._original.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(self._original)

        # -- Single control row: Tag selector + status + Polish ----------------
        control_row = QHBoxLayout()
        control_row.setSpacing(8)

        # Tag box: swaps between the combo (idle) and a greyed "Thinking…"
        # label (while polishing) so the tag name visibly disappears.
        self._tag_stack = QStackedWidget()
        self._tag_stack.setFixedHeight(34)
        self._tag_stack.setMaximumWidth(126)

        self._tag_combo = MarqueeComboBox()
        self._tag_combo.setMinimumWidth(92)
        self._tag_combo.setMaximumWidth(126)
        self._refresh_tag_combo()

        self._tag_thinking_label = QLabel("Thinking…")
        self._tag_thinking_label.setObjectName("TagThinking")
        self._tag_thinking_label.setAlignment(Qt.AlignCenter)

        self._tag_stack.addWidget(self._tag_combo)          # index 0: idle
        self._tag_stack.addWidget(self._tag_thinking_label)  # index 1: loading
        control_row.addWidget(self._tag_stack)

        spinner_wrap = QWidget()
        spinner_layout = QVBoxLayout(spinner_wrap)
        spinner_layout.setContentsMargins(0, 0, 0, 0)
        spinner_layout.setAlignment(Qt.AlignCenter)
        self._plus_spinner = Spinner(size=20)
        spinner_layout.addWidget(self._plus_spinner)
        self._plus_spinner.hide()
        control_row.addWidget(spinner_wrap)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            "color: #1a5a1a; font-size: 13px; font-weight: 600; font-family: 'Comfortaa';"
        )
        control_row.addWidget(self._status_label, 1)

        self._correct_btn = QPushButton("Polish")
        self._correct_btn.setObjectName("Primary")
        self._correct_btn.setFixedHeight(40)
        self._correct_btn.setMinimumWidth(100)
        control_row.addWidget(self._correct_btn)

        root.addLayout(control_row)

        # Improved pane header
        imp_hdr = QHBoxLayout()
        imp_hdr.addWidget(self._make_pane_label("Improved"))
        imp_hdr.addStretch(1)

        self._imp_expand_btn = HoverIconButton(norm_exp, hov_exp)
        self._imp_expand_btn.setFixedSize(24, 24)
        self._imp_expand_btn.setToolTip("Expand improved text view")
        self._imp_expand_btn.setStyleSheet("background: transparent; border: none;")
        self._imp_expand_btn.clicked.connect(self._on_expand_improved)
        imp_hdr.addWidget(self._imp_expand_btn)
        root.addLayout(imp_hdr)

        self._improved = QTextEdit()
        self._improved.setObjectName("ImprovedPane")
        self._improved.setReadOnly(True)
        self._improved.setFixedHeight(120)
        self._improved.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._improved.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(self._improved)

        # Edit, Copy & Replace row
        replace_row = QHBoxLayout()
        replace_row.setSpacing(10)
        replace_row.addStretch(1)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setObjectName("Secondary")
        self._edit_btn.setEnabled(False)
        self._edit_btn.setFixedHeight(40)
        self._edit_btn.setMinimumWidth(85)
        replace_row.addWidget(self._edit_btn)

        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setObjectName("Secondary")
        self._copy_btn.setEnabled(False)
        self._copy_btn.setFixedHeight(40)
        self._copy_btn.setMinimumWidth(85)
        replace_row.addWidget(self._copy_btn)

        self._replace_btn = QPushButton("Replace")
        self._replace_btn.setObjectName("Replace")
        self._replace_btn.setEnabled(False)
        self._replace_btn.setFixedHeight(40)
        self._replace_btn.setMinimumWidth(110)
        replace_row.addWidget(self._replace_btn)
        root.addLayout(replace_row)

    def _make_pane_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("PaneLabel")
        return label

    def _wire_signals(self) -> None:
        self._close_btn.clicked.connect(self.hide_window)
        self._settings_btn.clicked.connect(self._on_open_settings_clicked)
        self._correct_btn.clicked.connect(self._on_correct_clicked)
        self._edit_btn.clicked.connect(self._on_edit_clicked)
        self._copy_btn.clicked.connect(self._on_copy_clicked)
        self._replace_btn.clicked.connect(self._on_replace_clicked)

    # -- Tag management -------------------------------------------------

    def _refresh_tag_combo(self, select: str | None = None) -> None:
        current = select or (self._tag_combo.currentText() if self._tag_combo.count() else None)
        self._tag_combo.blockSignals(True)
        self._tag_combo.clear()
        names = self._tag_store.names()
        self._tag_combo.addItems(names)
        if current and current in names:
            self._tag_combo.setCurrentText(current)
        elif names:
            self._tag_combo.setCurrentIndex(0)
        self._tag_combo.blockSignals(False)
        self._tag_combo._sync_scroll_state()

    def open_settings(self, page: str = "Edit Tag") -> None:
        """Open Settings window (mutual exclusion: hides BetterIt window while Settings is open)."""
        if self._settings_window is None:
            self._settings_window = SettingsWindow(self._tag_store, initial_page=page)
            self._settings_window.tags_changed.connect(self._on_tags_changed_externally)
            self._settings_window.return_requested.connect(self._on_return_from_settings)
            # When settings fully closes (not just minimized), restore the BetterIt window
            self._settings_window.finished.connect(self._on_settings_closed)
        else:
            self._settings_window.open_page(page)

        # Show Return button because Settings was opened from BetterIt window
        self._settings_window.set_return_visible(True)

        # Mutual exclusion: hide the BetterIt window while Settings is up
        self.hide()

        screen = self.screen() or self._settings_window.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            self._settings_window.move(
                geo.center().x() - self._settings_window.width() // 2,
                geo.center().y() - self._settings_window.height() // 2,
            )
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

    def _on_return_from_settings(self) -> None:
        """Called when user clicks Return in Settings to go back to BetterIt."""
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_settings_closed(self) -> None:
        """Called when the Settings dialog is fully closed (not minimized)."""
        # Don't auto-show; user will trigger via hotkey or tray again.
        pass

    def show_for_text(self, text: str) -> None:
        """Populate the original pane and show the window centered; hide Settings first."""
        # Mutual exclusion: hide settings if it's open
        if self._settings_window is not None and self._settings_window.isVisible():
            self._settings_window.hide()

        self._original_label.setText("Original")
        self._original.setReadOnly(True)
        self._original.setPlainText(text)
        self._improved.clear()
        self._improved.setProperty("state", "")
        self._status_label.setText("")
        self._edit_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
        self._copy_btn.setText("Copy")
        self._replace_btn.setEnabled(False)
        self._correct_btn.setEnabled(True)
        self._end_loading_visuals()

        # Select default tag from configuration if present
        default_tag = self._tag_store.get_config("default_tag")
        if default_tag and default_tag in self._tag_store.names():
            self._refresh_tag_combo(select=default_tag)

        # Center on primary screen
        screen = self.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )
        self.show()

    def _on_open_settings_clicked(self) -> None:
        self.open_settings("Edit Tag")

    def _on_tags_changed_externally(self) -> None:
        self._refresh_tag_combo(select=self._tag_combo.currentText())


    # -- Drag implementation -------------------------------------------------

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

    # -- Public API ---------------------------------------------------------


    def show_loading(self) -> None:
        """Switch to loading state: tag box greyed + 'Thinking…', Polish button disabled."""
        self._correct_btn.setEnabled(False)
        self._correct_btn.setText("Polishing…")
        self._edit_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
        self._replace_btn.setEnabled(False)
        self._status_label.setText("")

        self._tag_combo.setEnabled(False)
        self._tag_stack.setCurrentWidget(self._tag_thinking_label)

        self._settings_btn.setEnabled(False)
        self._plus_spinner.show()
        self._plus_spinner.start()

    def show_improved(self, corrected: str) -> None:
        """Switch to result state: improved text shown, Edit, Copy and Replace enabled."""
        self._end_loading_visuals()
        self._status_label.setText("done")
        self._improved.setProperty("state", "")
        self._improved.setPlainText(corrected)
        self._edit_btn.setEnabled(True)
        self._copy_btn.setEnabled(True)
        self._copy_btn.setText("Copy")
        self._replace_btn.setEnabled(True)
        self._correct_btn.setEnabled(True)

    def show_error(self, message: str) -> None:
        """Switch to error state: red message, no Replace."""
        self._end_loading_visuals()
        self._status_label.setText("error")
        self._improved.setProperty("state", "error")
        self._improved.setPlainText(message)
        self._edit_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
        self._replace_btn.setEnabled(False)
        self._correct_btn.setEnabled(True)

    def _end_loading_visuals(self) -> None:
        self._plus_spinner.stop()
        self._plus_spinner.hide()
        self._settings_btn.setEnabled(True)

        self._tag_stack.setCurrentWidget(self._tag_combo)
        self._tag_combo.setEnabled(True)

        self._correct_btn.setText("Polish")

    def hide_window(self) -> None:
        """Hide and reset for the next invocation."""
        self._end_loading_visuals()
        self._reset_to_idle()
        self.hide()
        self.closed.emit()

    def _reset_to_idle(self) -> None:
        self._original_label.setText("Original")
        self._original.setReadOnly(True)
        self._original.clear()
        self._improved.clear()
        self._improved.setProperty("state", "")
        self._status_label.setText("")
        self._correct_btn.setEnabled(True)
        self._edit_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
        self._copy_btn.setText("Copy")
        self._replace_btn.setEnabled(False)
        self._end_loading_visuals()

    # -- Internal slots -----------------------------------------------------

    def _on_expand_original(self) -> None:
        title = self._original_label.text()
        overlay = ExpandOverlay(
            target_edit=self._original,
            parent_container=self._container,
            title_text=f"{title} Text  •  Expanded View",
            start_widget=self._original,
        )
        overlay.animate_expand()

    def _on_expand_improved(self) -> None:
        overlay = ExpandOverlay(
            target_edit=self._improved,
            parent_container=self._container,
            title_text="Improved Text  •  Expanded View",
            start_widget=self._improved,
        )
        overlay.animate_expand()

    def _on_edit_clicked(self) -> None:
        text = self._improved.toPlainText()
        if not text:
            return
        self._original.setReadOnly(False)
        self._original.setPlainText(text)
        self._original_label.setText("EDITING")
        self._original.setFocus()

    def _on_correct_clicked(self) -> None:
        text = self._original.toPlainText().strip()
        if not text:
            return
        tag_name = self._tag_combo.currentText()
        prompt = self._tag_store.prompt_for(tag_name)
        self.show_loading()
        self.correct_requested.emit(text, prompt)

    def _on_copy_clicked(self) -> None:
        text = self._improved.toPlainText()
        if not text:
            return
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)
        self._copy_btn.setText("Copied!")
        self._status_label.setText("copied")
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("Copy"))

    def _on_replace_clicked(self) -> None:
        text = self._improved.toPlainText()
        if not text:
            return
        self.replace_requested.emit(text)

    # -- Keyboard handling --------------------------------------------------

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.hide_window()
            event.accept()
            return
        # Ctrl+Enter to trigger Polish
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and (event.modifiers() & Qt.ControlModifier):
            if self._correct_btn.isEnabled():
                self._on_correct_clicked()
                event.accept()
                return
        super().keyPressEvent(event)

    # -- Rounded corners for transparency -----------------------------------

    def paintEvent(self, event) -> None:
        """Ensure the window has fully rounded corners with transparency."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, CORNER_RADIUS, CORNER_RADIUS)

        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        painter.setClipPath(path)
        painter.end()


# --- Bundled fonts -----------------------------------------------------------

def load_fonts() -> None:
    """Load BetterIt's bundled fonts without requiring system installation."""
    from pathlib import Path

    base_dir = Path(__file__).resolve().parent
    fonts_dir = base_dir / "fonts"
    if not fonts_dir.exists():
        # Check parent directories (e.g. project root)
        alt_dir = base_dir.parent.parent / "fonts"
        if alt_dir.exists():
            fonts_dir = alt_dir

    font_files = [
        fonts_dir / "Comfortaa" / "Comfortaa-VariableFont_wght.ttf",
        fonts_dir / "Playwrite_US_Modern" / "PlaywriteUSModern.ttf",
    ]

    comfortaa_static = fonts_dir / "Comfortaa" / "static" / "Comfortaa-Regular.ttf"
    playwrite_static = fonts_dir / "Playwrite_US_Modern" / "static" / "PlaywriteUSModern-Regular.ttf"

    if font_files[0].exists():
        QFontDatabase.addApplicationFont(str(font_files[0]))
    elif comfortaa_static.exists():
        QFontDatabase.addApplicationFont(str(comfortaa_static))

    if font_files[1].exists():
        QFontDatabase.addApplicationFont(str(font_files[1]))
    elif playwrite_static.exists():
        QFontDatabase.addApplicationFont(str(playwrite_static))


# --- Demo / Standalone runner -----------------------------------------------

class DemoWindow(QWidget):
    """A simple demo window to test the FloatingWindow."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Floating Window Demo")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Click the button to show the floating window:"))

        self.demo_text = QTextEdit()
        self.demo_text.setPlainText("This is a demo sentence with bad grammar and spelling errors.")
        layout.addWidget(self.demo_text)

        show_btn = QPushButton("Show Floating Window")
        show_btn.clicked.connect(self._show_floating)
        layout.addWidget(show_btn)

        self.floating = FloatingWindow()
        self.floating.correct_requested.connect(self._on_correct_requested)
        self.floating.replace_requested.connect(self._on_replace_requested)

    def _show_floating(self) -> None:
        text = self.demo_text.toPlainText()
        if text:
            self.floating.show_for_text(text)

    def _on_correct_requested(self, text: str, prompt: str) -> None:
        # Simulate LLM processing (in the real app, `prompt` would be sent
        # to the LLM along with `text` to steer the rewrite for this tag).
        QTimer.singleShot(1500, lambda: self._simulate_response(text))

    def _simulate_response(self, text: str) -> None:
        # Simple "correction" (just uppercase first letter of each word)
        corrected = " ".join(word.capitalize() for word in text.split())
        self.floating.show_improved(corrected)

    def _on_replace_requested(self, text: str) -> None:
        self.demo_text.setPlainText(text)
        self.floating.hide_window()


def main() -> None:
    """Main entry point for standalone testing."""
    app = QApplication(sys.argv)

    demo = DemoWindow()
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
