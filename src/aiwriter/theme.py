"""Shared green-theme stylesheet and visual identity for BetterIt windows."""

STYLESHEET = """
/* === Window Containers === */
QWidget#FloatingWindow, QWidget#SettingsWindow {
    background-color: rgba(240, 255, 240, 0.96);
    border: 3px solid #0a0a0a;
    border-radius: 28px;
}

QDialog#SettingsDialog {
    background-color: transparent;
}

/* === Headers & Typography === */
QLabel#Title {
    color: #0a2e0a;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 0 2px 2px 2px;
    font-family: 'Playwrite US Modern', 'Comfortaa', sans-serif;
}

QLabel#SettingsTitle {
    color: #0a2e0a;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.5px;
    font-family: 'Playwrite US Modern', 'Comfortaa', sans-serif;
}

QLabel#PaneLabel, QLabel#SectionLabel {
    color: #1a5a1a;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: 'Comfortaa';
}

QLabel#SubLabel {
    color: #386038;
    font-size: 12px;
    font-weight: 500;
    font-family: 'Comfortaa';
}

/* === Cards & Panels === */
QFrame#SettingsCard {
    background-color: rgba(255, 255, 255, 0.65);
    border: 2px solid #0a0a0a;
    border-radius: 20px;
    padding: 16px;
}

QFrame#InnerCard {
    background-color: rgba(235, 248, 235, 0.8);
    border: 1.5px solid #0a0a0a;
    border-radius: 14px;
    padding: 12px;
}

/* === Sidebar Navigation === */
QListWidget#Sidebar {
    background-color: rgba(226, 244, 226, 0.9);
    border: 2.5px solid #0a0a0a;
    border-radius: 20px;
    padding: 8px;
    font-family: 'Comfortaa';
    outline: none;
}

QListWidget#Sidebar::item {
    color: #1a5a1a;
    padding: 12px 14px;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 6px;
    border: 1.5px solid transparent;
}

QListWidget#Sidebar::item:hover {
    background-color: rgba(168, 213, 168, 0.45);
    border-color: rgba(10, 10, 10, 0.2);
}

QListWidget#Sidebar::item:selected {
    background-color: #1b5e20;
    color: #ffffff;
    border-color: #0a0a0a;
}

/* === Tag List === */
QListWidget#TagList {
    background-color: rgba(255, 255, 255, 0.9);
    border: 2px solid #0a0a0a;
    border-radius: 18px;
    padding: 6px;
    font-family: 'Comfortaa';
    outline: none;
}

QListWidget#TagList::item {
    color: #0a2e0a;
    padding: 10px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 4px;
    border: 1.5px solid transparent;
}

QListWidget#TagList::item:hover {
    background-color: rgba(168, 213, 168, 0.35);
    border-color: rgba(10, 10, 10, 0.2);
}

QListWidget#TagList::item:selected {
    background-color: #2e7d32;
    color: #ffffff;
    font-weight: 700;
    border-color: #0a0a0a;
}

/* === Text Inputs === */
QTextEdit {
    background-color: rgba(255, 255, 255, 0.92);
    color: #0a1a0a;
    border: 2px solid #0a0a0a;
    border-radius: 18px;
    padding: 12px 14px;
    font-size: 13px;
    selection-background-color: #4caf84;
    selection-color: #ffffff;
    font-family: 'Comfortaa';
}

QTextEdit:focus {
    border: 2.5px solid #1b5e20;
    background-color: #ffffff;
}

QTextEdit#ImprovedPane[state="error"] {
    color: #c0392b;
    border-color: #c0392b;
    background-color: rgba(255, 230, 230, 0.9);
}

QLineEdit {
    background-color: rgba(255, 255, 255, 0.92);
    color: #0a1a0a;
    border: 2px solid #0a0a0a;
    border-radius: 15px;
    padding: 9px 14px;
    font-size: 13px;
    font-family: 'Comfortaa';
    selection-background-color: #4caf84;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 2.5px solid #1b5e20;
    background-color: #ffffff;
}

/* === Combo Boxes === */
QComboBox {
    background-color: rgba(255, 255, 255, 0.92);
    color: #0a2e0a;
    border: 2px solid #0a0a0a;
    border-radius: 16px;
    padding: 7px 12px;
    font-size: 12px;
    font-weight: 700;
    font-family: 'Comfortaa';
}

QComboBox:hover {
    border-color: #0a0a0a;
    background-color: #ffffff;
}

QComboBox:focus {
    border: 2.5px solid #1b5e20;
}

QComboBox:disabled {
    background-color: rgba(210, 225, 210, 0.6);
    color: #6d8f6d;
    border-color: #55605c;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
    margin-right: 4px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0a2e0a;
    border: 2px solid #0a0a0a;
    border-radius: 14px;
    selection-background-color: #2e7d32;
    selection-color: #ffffff;
    outline: none;
    padding: 6px;
    font-family: 'Comfortaa';
    font-size: 12px;
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

/* === Check Boxes === */
QCheckBox {
    color: #0a2e0a;
    font-size: 13px;
    font-weight: 600;
    font-family: 'Comfortaa';
    spacing: 10px;
}

QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border: 2px solid #0a0a0a;
    border-radius: 7px;
    background-color: rgba(255, 255, 255, 0.95);
}

QCheckBox::indicator:hover {
    border-color: #1b5e20;
    background-color: #eef7ee;
}

QCheckBox::indicator:checked {
    background-color: #1b5e20;
    border-color: #0a0a0a;
}

/* === Buttons === */
QPushButton {
    background-color: #2e7d32;
    color: #ffffff;
    border: 2.5px solid #0a0a0a;
    border-radius: 19px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 700;
    font-family: 'Comfortaa';
    outline: none;
}

QPushButton:hover {
    background-color: #388e3c;
    border-color: #0a0a0a;
}

QPushButton:pressed {
    background-color: #1b5e20;
}

QPushButton:disabled {
    background-color: #7daa8a;
    color: #d4e8d4;
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

QPushButton#Secondary {
    background-color: rgba(255, 255, 255, 0.92);
    color: #1b5e20;
    border: 2px solid #0a0a0a;
}

QPushButton#Secondary:hover {
    background-color: #a8d5a8;
    color: #0a2e0a;
}

QPushButton#Secondary:pressed {
    background-color: #8ac58a;
}

QPushButton#Danger {
    background-color: #c0392b;
    color: #ffffff;
    border-color: #0a0a0a;
}

QPushButton#Danger:hover {
    background-color: #e74c3c;
}

QPushButton#Danger:pressed {
    background-color: #962d22;
}

QPushButton#Danger:disabled {
    background-color: #b87b74;
    color: #f0d5d2;
    border-color: #4a2d2a;
}

QPushButton#CloseButton {
    background-color: #e5e7eb;
    color: #374151;
    border: none;
    font-size: 15px;
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
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
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

QPushButton#ViewToggle {
    background-color: rgba(255, 255, 255, 0.85);
    color: #1a5a1a;
    border: 1.5px solid #0a0a0a;
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 700;
    font-family: 'Comfortaa';
    min-height: 24px;
}

QPushButton#ViewToggle:hover {
    background-color: #a8d5a8;
}

QPushButton#ViewToggle:checked {
    background-color: #1b5e20;
    color: #ffffff;
    border: 1.5px solid #0a0a0a;
}

/* === Scrollbars === */
QScrollBar:vertical {
    background: rgba(200, 230, 200, 0.3);
    width: 9px;
    border-radius: 4.5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #2e7d32;
    border-radius: 4.5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #1b5e20;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: rgba(200, 230, 200, 0.3);
    height: 9px;
    border-radius: 4.5px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #2e7d32;
    border-radius: 4.5px;
    min-width: 24px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
