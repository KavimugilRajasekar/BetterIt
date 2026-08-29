"""Shared green-theme stylesheet and visual identity for BetterIt windows."""

STYLESHEET = """
/* === Window Containers === */
QWidget#FloatingWindow, QWidget#SettingsWindow {
    background-color: rgba(240, 255, 240, 0.96);
    border: 3px solid #0a0a0a;
    border-radius: 28px;
}

QWidget#ThemedPopupContainer {
    background-color: rgba(242, 255, 242, 0.98);
    border: 3px solid #0a0a0a;
    border-radius: 24px;
}

QDialog#SettingsDialog, QDialog#ThemedDialog {
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

QLabel#PopupTitle {
    color: #0a2e0a;
    font-size: 17px;
    font-weight: 700;
    font-family: 'Comfortaa';
}

QLabel#PopupMessage {
    color: #1a3a1a;
    font-size: 13px;
    font-weight: 500;
    font-family: 'Comfortaa';
}

QLabel#PaneLabel, QLabel#SectionLabel {
    color: #1a5a1a;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: 'Comfortaa';
}

QLabel#CardTitle {
    color: #0a2e0a;
    font-size: 15px;
    font-weight: 700;
    font-family: 'Comfortaa';
}

QLabel#SubLabel {
    color: #386038;
    font-size: 12px;
    font-weight: 500;
    font-family: 'Comfortaa';
}

QLabel#ModelNameLabel {
    color: #0a2e0a;
    font-size: 12px;
    font-weight: 700;
    font-family: 'Comfortaa';
}

QLabel#ActiveBadge {
    background-color: #1b5e20;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    border-radius: 12px;
    padding: 4px 10px;
    font-family: 'Comfortaa';
}

QLabel#ModelActiveBadge {
    background-color: #2e7d32;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    border-radius: 10px;
    padding: 3px 8px;
    font-family: 'Comfortaa';
}

QLabel#AboutHeroLabel {
    color: #0a2e0a;
    font-size: 18px;
    font-weight: 700;
    font-family: 'Playwrite US Modern', 'Comfortaa';
}

QLabel#AboutStepLabel {
    color: #0a2e0a;
    font-size: 13px;
    font-weight: 700;
    font-family: 'Comfortaa';
}

QLabel#AboutStepDesc {
    color: #2e5a2e;
    font-size: 12px;
    font-weight: 500;
    font-family: 'Comfortaa';
    line-height: 1.4;
}

QLabel#AboutVersion {
    color: #4a7a4a;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Comfortaa';
}

QLabel#AboutIconLabel {
    font-size: 24px;
    color: #1b5e20;
}

/* === Cards & Panels === */
QFrame#SettingsCard {
    background-color: rgba(255, 255, 255, 0.70);
    border: 2.5px solid #0a0a0a;
    border-radius: 22px;
    padding: 16px;
}

QFrame#SingleWhiteCard {
    background-color: #ffffff;
    border: 2.5px solid #0a0a0a;
    border-radius: 22px;
    padding: 18px;
}

QFrame#KeyProfileCard {
    background-color: #ffffff;
    border: 2.5px solid #0a0a0a;
    border-radius: 20px;
    padding: 16px;
}

QFrame#KeyProfileCard[active="true"] {
    background-color: #ffffff;
    border: 2.5px solid #1b5e20;
    border-radius: 20px;
    padding: 16px;
}

QFrame#NewProfileCard {
    background-color: rgba(240, 255, 240, 0.95);
    border: 2.5px dashed #1b5e20;
    border-radius: 20px;
    padding: 16px;
}

QFrame#ModelRowFrame {
    background-color: rgba(244, 252, 244, 0.9);
    border: 1.5px solid #0a0a0a;
    border-radius: 14px;
    padding: 6px 10px;
}

QFrame#ModelRowFrame[selected="true"] {
    background-color: rgba(226, 248, 226, 0.98);
    border: 2px solid #1b5e20;
    border-radius: 14px;
    padding: 6px 10px;
}

QFrame#InnerCard {
    background-color: rgba(235, 248, 235, 0.85);
    border: 2px solid #0a0a0a;
    border-radius: 18px;
    padding: 14px;
}

QFrame#StatusBanner {
    background-color: rgba(240, 252, 240, 0.95);
    border: 2px solid #0a0a0a;
    border-radius: 16px;
    padding: 8px 12px;
}

QFrame#AboutStepCard {
    background-color: rgba(255, 255, 255, 0.80);
    border: 2px solid rgba(10, 10, 10, 0.35);
    border-radius: 18px;
    padding: 12px;
}

QFrame#AboutStepCard[active="true"] {
    background-color: rgba(220, 250, 220, 0.98);
    border: 2.5px solid #1b5e20;
    border-radius: 18px;
}

QFrame#AboutHeroCard {
    background-color: rgba(215, 245, 215, 0.85);
    border: 2.5px solid #0a0a0a;
    border-radius: 22px;
    padding: 18px;
}

/* === Sidebar Navigation === */
QListWidget#Sidebar {
    background-color: rgba(226, 244, 226, 0.92);
    border: 2.5px solid #0a0a0a;
    border-radius: 22px;
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
    background-color: rgba(255, 255, 255, 0.92);
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
    background-color: rgba(255, 255, 255, 0.95);
    color: #0a1a0a;
    border: 2px solid #0a0a0a;
    border-radius: 16px;
    padding: 8px 14px;
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
    background-color: rgba(255, 255, 255, 0.95);
    color: #0a2e0a;
    border: 2px solid #0a0a0a;
    border-radius: 16px;
    padding: 8px 14px;
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
    width: 24px;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0a2e0a;
    border: 2px solid #0a0a0a;
    border-radius: 16px;
    selection-background-color: #2e7d32;
    selection-color: #ffffff;
    outline: none;
    padding: 8px;
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
    border-radius: 18px;
    padding: 7px 16px;
    font-size: 12px;
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
    border-radius: 16px;
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
    border-radius: 16px;
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

QPushButton#DangerIcon {
    background-color: #fee2e2;
    color: #dc2626;
    border: 1.5px solid #dc2626;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 700;
    padding: 0px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
}

QPushButton#DangerIcon:hover {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#DangerIcon:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
    border-color: #d1d5db;
}

QPushButton#MiniAction {
    background-color: #ffffff;
    color: #1b5e20;
    border: 1.5px solid #0a0a0a;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    min-height: 26px;
}

QPushButton#MiniAction:hover {
    background-color: #a8d5a8;
    color: #0a2e0a;
}

QPushButton#ModelTestBtn {
    background-color: #1b5e20;
    color: #ffffff;
    border: 1.5px solid #0a0a0a;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    min-height: 26px;
}

QPushButton#ModelTestBtn:hover {
    background-color: #2e7d32;
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

QPushButton#MinimizeButton {
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

QPushButton#MinimizeButton:hover {
    color: #ffffff;
    background-color: #1b5e20;
}

QPushButton#MinimizeButton:pressed {
    background-color: #0d3d12;
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
    background-color: rgba(255, 255, 255, 0.88);
    color: #1a5a1a;
    border: 1.5px solid #0a0a0a;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    font-family: 'Comfortaa';
    min-height: 26px;
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
    width: 8px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #2e7d32;
    border-radius: 4px;
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
    height: 8px;
    border-radius: 4px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: #2e7d32;
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === Scroll Area === */
QScrollArea {
    border: none;
    background: transparent;
    border-radius: 20px;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}
"""
