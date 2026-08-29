"""Shared green-theme stylesheet for BetterIt's windows."""

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

QLineEdit {
    background-color: rgba(255, 255, 255, 0.88);
    color: #0a1a0a;
    border: 2px solid #0a0a0a;
    border-radius: 14px;
    padding: 8px 12px;
    font-size: 13px;
    font-family: 'Comfortaa';
}

QComboBox {
    background-color: rgba(255, 255, 255, 0.9);
    color: #0a2e0a;
    border: 2px solid #0a0a0a;
    border-radius: 16px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 700;
    font-family: 'Comfortaa';
}

QComboBox:hover {
    border-color: #0a0a0a;
    background-color: rgba(255, 255, 255, 1.0);
}

QComboBox:disabled {
    background-color: rgba(210, 225, 210, 0.6);
    color: #6d8f6d;
    border-color: #55605c;
}

QComboBox::drop-down {
    border: none;
    width: 18px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0a2e0a;
    border: 2px solid #0a0a0a;
    border-radius: 8px;
    selection-background-color: #a8d5a8;
    outline: none;
    padding: 4px;
}

QLabel#TagThinking {
    background-color: rgba(210, 225, 210, 0.7);
    border: 2px solid #0a0a0a;
    border-radius: 16px;
    color: #4a6a4a;
    font-size: 12px;
    font-weight: 700;
    font-family: 'Comfortaa';
    padding: 6px 10px;
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
    background-color: #e5e7eb;
    color: #374151;
    border: none;
    font-size: 16px;
    font-weight: 700;
    padding: 0;
    border-radius: 15px;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
}

QPushButton#CloseButton:hover {
    color: #ffffff;
    background-color: #ef4444;
}

QPushButton#CloseButton:pressed {
    background-color: #dc2626;
}

QPushButton#IconButton {
    background-color: rgba(255, 255, 255, 0.92);
    color: #1b5e20;

    border: 2px solid #0a0a0a;
    border-radius: 16px;

    padding: 0px;
    margin: 0px;

    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;

    font-family: 'Comfortaa';
    font-size: 18px;
    font-weight: 700;
}

QPushButton#IconButton:hover {
    background-color: #a8d5a8;
    border: 2px solid #0a0a0a;
}

QPushButton#IconButton:pressed {
    background-color: #7fbd7f;
    border: 2px solid #0a0a0a;
}

QPushButton#IconButton:disabled {
    background-color: rgba(210, 225, 210, 0.6);
    color: #6d8f6d;
    border: 2px solid #55605c;
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
