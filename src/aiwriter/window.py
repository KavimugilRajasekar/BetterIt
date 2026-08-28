"""The always-on-top floating window shown when the hotkey fires."""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# --- Styling ----------------------------------------------------------------

# Dark palette — feels like a native AI popover rather than a window.
STYLESHEET = """
QWidget#FloatingWindow {
    background-color: #1f2024;
    border: 1px solid #2c2e33;
    border-radius: 12px;
}
QLabel#Title {
    color: #f0f1f4;
    font-size: 13px;
    font-weight: 600;
    padding: 4px 0;
}
QLabel#PaneLabel {
    color: #8a8d94;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QTextEdit {
    background-color: #16171a;
    color: #e6e7ea;
    border: 1px solid #2c2e33;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
    selection-background-color: #3a4358;
}
QTextEdit#ImprovedPane[state="error"] {
    color: #ff7a7a;
}
QPushButton {
    background-color: #3a4358;
    color: #f0f1f4;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover { background-color: #46516b; }
QPushButton:pressed { background-color: #2f374a; }
QPushButton:disabled { background-color: #2a2c31; color: #6a6d74; }
QPushButton#Primary {
    background-color: #5b8def;
    color: white;
}
QPushButton#Primary:hover { background-color: #6f9bf5; }
QPushButton#Primary:pressed { background-color: #4a7ad8; }
QPushButton#CloseButton {
    background-color: transparent;
    color: #8a8d94;
    padding: 2px 8px;
    font-size: 16px;
}
QPushButton#CloseButton:hover { color: #f0f1f4; }
"""


# --- Custom widgets ---------------------------------------------------------

class Spinner(QWidget):
    """A tiny dependency-free rotating-arc spinner."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self.setFixedSize(18, 18)
        self.hide()

    def start(self) -> None:
        self._angle = 0
        self.show()
        self._timer.start(60)

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _advance(self) -> None:
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Faint track
        pen = QPen(QColor("#3a4358"), 2)
        painter.setPen(pen)
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)
        # Bright arc
        pen = QPen(QColor("#5b8def"), 2)
        painter.setPen(pen)
        # Draw an arc covering (360 - 90) degrees starting at `_angle`.
        start = self._angle * 16  # 1/16 of a degree
        span = (360 - 90) * 16
        painter.drawArc(2, 2, self.width() - 4, self.height() - 4, start, span)


# --- Main window ------------------------------------------------------------

class FloatingWindow(QWidget):
    """The 'cutie' window: shows original text, runs grammar, shows replacement."""

    # Signals — the owning app connects these to the LLM worker / paste-back.
    correct_requested = Signal(str)  # emits the original text
    replace_requested = Signal(str)  # emits the corrected text
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setObjectName("FloatingWindow")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(QSize(420, 380))
        self.setStyleSheet(STYLESHEET)

        self._build_ui()
        self._wire_signals()
        self._reset_to_idle()

    # -- UI construction ----------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        self._title = QLabel("AI Writing Assistant")
        self._title.setObjectName("Title")
        title_row.addWidget(self._title)
        title_row.addStretch(1)
        self._close_btn = QPushButton("×")  # ×
        self._close_btn.setObjectName("CloseButton")
        self._close_btn.setFixedWidth(28)
        title_row.addWidget(self._close_btn)
        root.addLayout(title_row)

        # Original pane
        root.addWidget(self._make_pane_label("Original"))
        self._original = QTextEdit()
        self._original.setReadOnly(True)
        self._original.setFixedHeight(80)
        root.addWidget(self._original)

        # Action row: spinner + primary button
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self._spinner = Spinner(self)
        action_row.addWidget(self._spinner)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #8a8d94; font-size: 12px;")
        action_row.addWidget(self._status_label, 1)
        self._correct_btn = QPushButton("Correct Grammar")
        self._correct_btn.setObjectName("Primary")
        action_row.addWidget(self._correct_btn)
        root.addLayout(action_row)

        # Improved pane
        root.addWidget(self._make_pane_label("Improved"))
        self._improved = QTextEdit()
        self._improved.setObjectName("ImprovedPane")
        self._improved.setReadOnly(True)
        self._improved.setFixedHeight(100)
        root.addWidget(self._improved)

        # Replace row
        replace_row = QHBoxLayout()
        replace_row.addStretch(1)
        self._replace_btn = QPushButton("Replace")
        self._replace_btn.setEnabled(False)
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

    # -- Public API used by the owning app ----------------------------------

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

        # Center on the primary screen.
        screen = self.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )
        self.show()

    def show_loading(self) -> None:
        """Switch to the loading state: spinner on, button disabled."""
        self._correct_btn.setEnabled(False)
        self._spinner.start()
        self._status_label.setText("Thinking…")
        self._replace_btn.setEnabled(False)

    def show_improved(self, corrected: str) -> None:
        """Switch to the result state: improved text shown, Replace enabled."""
        self._spinner.stop()
        self._status_label.setText("Done.")
        self._improved.setProperty("state", "")
        self._improved.setPlainText(corrected)
        self._replace_btn.setEnabled(True)
        self._correct_btn.setEnabled(True)

    def show_error(self, message: str) -> None:
        """Switch to the error state: red message, no Replace."""
        self._spinner.stop()
        self._status_label.setText("Error")
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

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.key() == Qt.Key_Escape:
            self.hide_window()
            event.accept()
            return
        super().keyPressEvent(event)
