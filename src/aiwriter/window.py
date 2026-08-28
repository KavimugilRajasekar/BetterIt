"""
The always-on-top floating window shown when the hotkey fires.
Drag & movable, fixed size, completely rounded corners,
green theme with slight transparency and clean layout.
"""

from __future__ import annotations

from pathlib import Path

import sys

from PySide6.QtCore import Qt, QTimer, QSize, Signal, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QMouseEvent, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# --- Styling ----------------------------------------------------------------

# Green theme with black border, fully rounded corners, slight transparency
STYLESHEET = """
QWidget#FloatingWindow {
    background-color: rgba(240, 255, 240, 0.92);
    border: 3px solid #0a0a0a;
    border-radius: 28px;
}

QLabel#Title {
    color: #0a2e0a;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 0 2px 2px 2px;
    font-family: 'Playwrite US Modern';
}

QLabel#PaneLabel {
    color: #1a5a1a;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: 'Comfortaa';
}

QTextEdit {
    background-color: rgba(255, 255, 255, 0.88);
    color: #0a1a0a;
    border: 2px solid #0a0a0a;
    border-radius: 18px;
    padding: 12px 14px;
    font-size: 13px;
    selection-background-color: #4caf84;
    font-family: 'Comfortaa';
}

QTextEdit:focus {
    border-color: #0a0a0a;
    border-width: 2px;
}

QTextEdit#ImprovedPane[state="error"] {
    color: #c0392b;
    border-color: #0a0a0a;
    background-color: rgba(255, 230, 230, 0.85);
}

QPushButton {
    background-color: #2e7d32;
    color: #ffffff;
    border: 2.5px solid #0a0a0a;
    border-radius: 20px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 700;
    font-family: 'Comfortaa';
}

QPushButton:hover {
    background-color: #388e3c;
    border-color: #0a0a0a;
}

QPushButton:pressed {
    background-color: #1b5e20;
}

QPushButton:disabled {
    background-color: #6d8f6d;
    color: #d4e0d4;
    border-color: #3a4a3a;
}

QPushButton#Primary {
    background-color: #1b5e20;
    color: #ffffff;
    border-color: #0a0a0a;
}

QPushButton#Primary:hover {
    background-color: #2e7d32;
}

QPushButton#Primary:pressed {
    background-color: #0d3d12;
}

QPushButton#CloseButton {
    background-color: transparent;
    color: #0a0a0a;
    border: 2px solid #0a0a0a;
    font-size: 18px;
    font-weight: 700;
    padding: 0;
    border-radius: 30px;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
}

QPushButton#CloseButton:hover {
    color: #ffffff;
    background-color: #c0392b;
    border-color: #0a0a0a;
}

QPushButton#Replace {
    background-color: #00a86b;
    color: #ffffff;
    border-color: #0a0a0a;
}

QPushButton#Replace:hover {
    background-color: #00c97a;
}

QPushButton#Replace:disabled {
    background-color: #7daa8a;
    color: #d4e8d4;
    border-color: #3a5a3a;
}

QScrollBar:vertical {
    background: rgba(200, 230, 200, 0.3);
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #2e7d32;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


# --- Custom widgets ---------------------------------------------------------

class Spinner(QWidget):
    """A tiny dependency-free rotating-arc spinner (green theme)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(20, 20)
        self.hide()

    def start(self) -> None:
        self._angle = 0
        self.show()
        self._timer.start(50)

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

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


# --- Main window ------------------------------------------------------------

class FloatingWindow(QWidget):
    """
    The 'cutie' window: shows original text, runs grammar, shows replacement.
    Draggable, fixed size, green theme, fully rounded corners.
    """

    # Signals — the owning app connects these to the LLM worker / paste-back.
    correct_requested = Signal(str)   # emits the original text
    replace_requested = Signal(str)   # emits the corrected text
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("FloatingWindow")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(QSize(440, 400))
        self.setMask(self._rounded_mask(440, 400, 28))
        
        # For dragging
        self._drag_pos: QPoint | None = None

        # Main container with rounded corners and transparency
        self._container = QWidget(self)
        self._container.setGeometry(0, 0, 440, 400)
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
        from PySide6.QtGui import QBitmap, QRegion

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
        self._title.setStyleSheet("""
            QLabel#Title {
            font-size: 26px;
            font-weight: 700;
            }
        """)
        # Make title area draggable
        self._title.mousePressEvent = self._mouse_press_event
        self._title.mouseMoveEvent = self._mouse_move_event
        title_row.addWidget(self._title)
        title_row.addStretch(1)
        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("CloseButton")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setStyleSheet("""
            QPushButton#CloseButton {
            border: none;
            border-radius: 15px;
            background-color: #e5e7eb;
            color: #374151;
            font-size: 16px;
            font-weight: bold;
            }

            QPushButton#CloseButton:hover {
            background-color: #ef4444;
            color: white;
            }

            QPushButton#CloseButton:pressed {
            background-color: #dc2626;
            color: white;
            }
        """)

        title_row.addWidget(self._close_btn)
        root.addLayout(title_row)

        # Original pane
        root.addWidget(self._make_pane_label("Original"))
        self._original = QTextEdit()
        self._original.setReadOnly(True)
        self._original.setFixedHeight(88)
        root.addWidget(self._original)

        # Action row: spinner + status + button
        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        self._spinner = Spinner(self._container)
        action_row.addWidget(self._spinner)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #1a5a1a; font-size: 13px; font-weight: 600; font-family: 'Comfortaa';")
        action_row.addWidget(self._status_label, 1)
        self._correct_btn = QPushButton("Polish")
        self._correct_btn.setObjectName("Primary")
        self._correct_btn.setFixedHeight(40)
        action_row.addWidget(self._correct_btn)
        root.addLayout(action_row)

        # Improved pane
        root.addWidget(self._make_pane_label("Improved"))
        self._improved = QTextEdit()
        self._improved.setObjectName("ImprovedPane")
        self._improved.setReadOnly(True)
        self._improved.setFixedHeight(108)
        root.addWidget(self._improved)

        # Replace row
        replace_row = QHBoxLayout()
        replace_row.addStretch(1)
        self._replace_btn = QPushButton("Replace")
        self._replace_btn.setObjectName("Replace")
        self._replace_btn.setEnabled(False)
        self._replace_btn.setFixedHeight(40)
        replace_row.addWidget(self._replace_btn)
        root.addLayout(replace_row)

    def _make_pane_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("PaneLabel")
        return label

    def _wire_signals(self) -> None:
        self._close_btn.clicked.connect(self.hide_window)
        self._correct_btn.clicked.connect(self._on_correct_clicked)
        self._replace_btn.clicked.connect(self._on_replace_clicked)

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

    def show_for_text(self, text: str) -> None:
        """Populate the original pane and show the window centered."""
        self._original.setPlainText(text)
        self._improved.clear()
        self._improved.setProperty("state", "")
        self._status_label.setText("")
        self._replace_btn.setEnabled(False)
        self._correct_btn.setEnabled(True)
        self._correct_btn.show()
        self._spinner.stop()

        # Center on primary screen
        screen = self.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )
        self.show()

    def show_loading(self) -> None:
        """Switch to loading state: spinner on, button disabled."""
        self._correct_btn.setEnabled(False)
        self._spinner.start()
        self._status_label.setText("thinking...")
        self._replace_btn.setEnabled(False)

    def show_improved(self, corrected: str) -> None:
        """Switch to result state: improved text shown, Replace enabled."""
        self._spinner.stop()
        self._status_label.setText("done")
        self._improved.setProperty("state", "")
        self._improved.setPlainText(corrected)
        self._replace_btn.setEnabled(True)
        self._correct_btn.setEnabled(True)

    def show_error(self, message: str) -> None:
        """Switch to error state: red message, no Replace."""
        self._spinner.stop()
        self._status_label.setText("error")
        self._improved.setProperty("state", "error")
        self._improved.setPlainText(message)
        self._replace_btn.setEnabled(False)
        self._correct_btn.setEnabled(True)

    def hide_window(self) -> None:
        """Hide and reset for the next invocation."""
        self._spinner.stop()
        self._reset_to_idle()
        self.hide()
        self.closed.emit()

    def _reset_to_idle(self) -> None:
        self._original.clear()
        self._improved.clear()
        self._improved.setProperty("state", "")
        self._status_label.setText("")
        self._correct_btn.setEnabled(True)
        self._replace_btn.setEnabled(False)

    # -- Internal slots -----------------------------------------------------

    def _on_correct_clicked(self) -> None:
        text = self._original.toPlainText().strip()
        if not text:
            return
        self.show_loading()
        self.correct_requested.emit(text)

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
        super().keyPressEvent(event)

    # -- Rounded corners for transparency -----------------------------------

    def paintEvent(self, event) -> None:
        """Ensure the window has fully rounded corners with transparency."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create a rounded rectangle path
        path = QPainterPath()
        rect = self.rect()
        radius = 20
        path.addRoundedRect(rect, radius, radius)
        
        # Fill with transparent background
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        
        # Set the clip path to keep everything within rounded corners
        painter.setClipPath(path)


# --- Bundled fonts -----------------------------------------------------------

def load_fonts() -> None:
    """Load BetterIt's bundled fonts without requiring system installation."""
    base_dir = Path(__file__).resolve().parent
    fonts_dir = base_dir / "fonts"

    font_files = [
        fonts_dir / "Comfortaa" / "Comfortaa-VariableFont_wght.ttf",
        fonts_dir / "Playwrite_US_Modern" / "PlaywriteUSModern.ttf",
    ]

    # Fall back to static files if a variable font is unavailable.
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
            
    def _on_correct_requested(self, text: str) -> None:
        # Simulate LLM processing
        self.floating.show_loading()
        
        # Simulate async response
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