"""
Briefly Modern UI Style System (Catppuccin Macchiato & Adwaita Dark Inspired)
High Contrast, Clean Typography, Resilient Component Styling.
"""

DARK_THEME_QSS = """
/* Global Window & Base Widgets */
QMainWindow, QDialog {
    background-color: #181926;
    color: #cad3f5;
}

QWidget {
    font-family: 'Cantarell', 'Ubuntu', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
    color: #cad3f5;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #181926;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #494d64;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #5b6078;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Splitter */
QSplitter::handle {
    background-color: #24273a;
    width: 2px;
}
QSplitter::handle:hover {
    background-color: #8aadf4;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #363a4f;
    background-color: #1e2030;
    border-radius: 8px;
    padding: 6px;
}

QTabBar::tab {
    background: #181926;
    color: #a5adcb;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #24273a;
    color: #8aadf4;
    border-bottom: 2px solid #8aadf4;
}

QTabBar::tab:hover:!selected {
    background: #1e2030;
    color: #cad3f5;
}

/* Buttons */
QPushButton {
    background-color: #24273a;
    color: #cad3f5;
    border: 1px solid #363a4f;
    padding: 7px 14px;
    border-radius: 6px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #363a4f;
    border-color: #494d64;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #494d64;
}

QPushButton:disabled {
    background-color: #1e2030;
    color: #6e738d;
    border-color: #24273a;
}

QPushButton#icon_btn {
    padding: 0px;
    font-size: 14px;
    font-weight: bold;
    text-align: center;
}

/* Primary Accent Action Buttons */
QPushButton#btn_primary_action {
    background-color: #8aadf4;
    color: #181926;
    border: none;
    font-weight: bold;
}
QPushButton#btn_primary_action:hover {
    background-color: #b7bdf8;
}

/* Record Button States */
QPushButton#btn_record_start {
    background-color: #a6da95;
    color: #181926;
    border: none;
    font-size: 14px;
    font-weight: bold;
    padding: 10px 18px;
    border-radius: 8px;
}
QPushButton#btn_record_start:hover {
    background-color: #8bd5ca;
}

QPushButton#btn_record_stop {
    background-color: #ed8796;
    color: #181926;
    border: none;
    font-size: 14px;
    font-weight: bold;
    padding: 10px 18px;
    border-radius: 8px;
}
QPushButton#btn_record_stop:hover {
    background-color: #ee99a0;
}

/* Inputs & Combos */
QComboBox, QLineEdit, QTextEdit {
    background-color: #1e2030;
    color: #cad3f5;
    border: 1px solid #363a4f;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #8aadf4;
    selection-color: #181926;
}

QComboBox:focus, QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #8aadf4;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1e2030;
    border: 1px solid #494d64;
    selection-background-color: #363a4f;
    selection-color: #8aadf4;
    border-radius: 6px;
    padding: 4px;
    color: #cad3f5;
}

/* Meeting List Widget */
QListWidget#meetings_list_widget {
    background-color: #1e2030;
    border: 1px solid #363a4f;
    border-radius: 8px;
    padding: 4px;
}

QListWidget#meetings_list_widget::item {
    border-radius: 6px;
    margin-bottom: 4px;
    padding: 4px;
}

QListWidget#meetings_list_widget::item:selected {
    background-color: #24273a;
    border-left: 3px solid #8aadf4;
}

QListWidget#meetings_list_widget::item:hover:!selected {
    background-color: #202334;
}

/* Cards & Frames */
QFrame#sidebar_frame {
    background-color: #181926;
    border-right: 1px solid #24273a;
}

QFrame#card_frame {
    background-color: #1e2030;
    border: 1px solid #363a4f;
    border-radius: 8px;
    padding: 12px;
}

QFrame#banner_frame {
    border-radius: 8px;
    padding: 8px 12px;
}

/* Typography Labels */
QLabel#lbl_timer_idle {
    font-size: 32px;
    font-weight: 700;
    font-family: 'Monospace', 'Courier New', monospace;
    color: #cad3f5;
}

QLabel#lbl_timer_recording {
    font-size: 32px;
    font-weight: 700;
    font-family: 'Monospace', 'Courier New', monospace;
    color: #ed8796;
}

QLabel#lbl_field_header {
    font-size: 12px;
    font-weight: 600;
    color: #b8c0e0;
}

QLabel#lbl_sidebar_title {
    font-size: 17px;
    font-weight: bold;
    color: #8aadf4;
}

QStatusBar {
    background-color: #141520;
    color: #a5adcb;
    border-top: 1px solid #24273a;
    padding: 4px 8px;
}
"""

MARKDOWN_HTML_STYLE = """
<style>
body {
    background-color: #1e2030;
    color: #cad3f5;
    font-family: 'Cantarell', 'Ubuntu', 'Inter', -apple-system, sans-serif;
    font-size: 14px;
    line-height: 1.65;
    padding: 16px;
}
h1 {
    color: #8aadf4;
    border-bottom: 2px solid #363a4f;
    padding-bottom: 8px;
    font-size: 24px;
    margin-top: 6px;
    margin-bottom: 16px;
    font-weight: 700;
}
h2 {
    color: #a6da95;
    border-bottom: 1px solid #363a4f;
    padding-bottom: 6px;
    font-size: 18px;
    margin-top: 22px;
    margin-bottom: 12px;
    font-weight: 600;
}
h3 {
    color: #f5a97f;
    font-size: 15px;
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    border-radius: 6px;
    overflow: hidden;
}
th, td {
    border: 1px solid #363a4f;
    padding: 10px 14px;
    text-align: left;
}
th {
    background-color: #24273a;
    color: #cdd6f4;
    font-weight: 700;
    font-size: 13px;
}
tr:nth-child(even) {
    background-color: #181926;
}
tr:hover {
    background-color: #24273a;
}
code {
    background-color: #24273a;
    color: #ed8796;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monospace', 'Courier New', monospace;
    font-size: 12px;
}
pre {
    background-color: #141520;
    border: 1px solid #363a4f;
    padding: 14px;
    border-radius: 6px;
    overflow-x: auto;
}
blockquote {
    border-left: 4px solid #8aadf4;
    background-color: #181926;
    margin: 12px 0;
    padding: 10px 16px;
    border-radius: 0 6px 6px 0;
    color: #b8c0e0;
}
ul, ol {
    padding-left: 24px;
    margin-top: 6px;
    margin-bottom: 12px;
}
li {
    margin-bottom: 6px;
}
strong {
    color: #ffffff;
}
</style>
"""
