"""
Modern Dark Theme inspired by GNOME Adwaita Dark and Catppuccin.
"""

DARK_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QWidget {
    font-family: 'Cantarell', 'Inter', 'Ubuntu', 'DejaVu Sans', sans-serif;
    font-size: 13px;
    color: #cdd6f4;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #181825;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #313244;
    background-color: #181825;
    border-radius: 8px;
    padding: 6px;
}

QTabBar::tab {
    background: #1e1e2e;
    color: #a6adc8;
    padding: 9px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: #313244;
    color: #89b4fa;
    border-bottom: 2px solid #89b4fa;
}

QTabBar::tab:hover:!selected {
    background: #252538;
    color: #cdd6f4;
}

/* Buttons */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}

QPushButton:pressed {
    background-color: #585b70;
}

QPushButton:disabled {
    background-color: #181825;
    color: #585b70;
    border-color: #313244;
}

/* Primary Record Button */
QPushButton#btn_record_start {
    background-color: #a6e3a1;
    color: #11111b;
    border: none;
    font-size: 15px;
    font-weight: bold;
    padding: 12px 24px;
    border-radius: 8px;
}
QPushButton#btn_record_start:hover {
    background-color: #94e2d5;
}

QPushButton#btn_record_stop {
    background-color: #f38ba8;
    color: #11111b;
    border: none;
    font-size: 15px;
    font-weight: bold;
    padding: 12px 24px;
    border-radius: 8px;
}
QPushButton#btn_record_stop:hover {
    background-color: #eba0ac;
}

/* Action Secondary Button */
QPushButton#btn_primary_action {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    font-weight: 600;
}
QPushButton#btn_primary_action:hover {
    background-color: #b4befe;
}

/* Inputs & Combos */
QComboBox, QLineEdit, QTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
}

QComboBox:focus, QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #89b4fa;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    border: 1px solid #45475a;
    selection-background-color: #313244;
    selection-color: #89b4fa;
    border-radius: 6px;
    padding: 4px;
}

/* Table View */
QTableWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    gridline-color: #313244;
    color: #cdd6f4;
    selection-background-color: #313244;
    selection-color: #89b4fa;
}

QHeaderView::section {
    background-color: #1e1e2e;
    color: #a6adc8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #313244;
    font-weight: 600;
}

/* Labels */
QLabel#lbl_timer {
    font-size: 38px;
    font-weight: 700;
    font-family: 'Monospace', 'Courier New', monospace;
    color: #f38ba8;
}

QLabel#lbl_card_title {
    font-size: 16px;
    font-weight: 600;
    color: #cdd6f4;
}

QFrame#card_frame {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 10px;
    padding: 16px;
}

QStatusBar {
    background-color: #11111b;
    color: #a6adc8;
    border-top: 1px solid #313244;
}
"""

MARKDOWN_HTML_STYLE = """
<style>
body {
    background-color: #181825;
    color: #cdd6f4;
    font-family: 'Cantarell', 'Ubuntu', 'Inter', -apple-system, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    padding: 12px;
}
h1 {
    color: #89b4fa;
    border-bottom: 2px solid #313244;
    padding-bottom: 6px;
    font-size: 24px;
    margin-top: 10px;
}
h2 {
    color: #a6e3a1;
    border-bottom: 1px solid #313244;
    padding-bottom: 4px;
    font-size: 18px;
    margin-top: 18px;
}
h3 {
    color: #fab387;
    font-size: 15px;
    margin-top: 14px;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 14px 0;
}
th, td {
    border: 1px solid #45475a;
    padding: 8px 12px;
    text-align: left;
}
th {
    background-color: #313244;
    color: #cdd6f4;
    font-weight: bold;
}
tr:nth-child(even) {
    background-color: #1e1e2e;
}
code {
    background-color: #313244;
    color: #f38ba8;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
}
pre {
    background-color: #11111b;
    border: 1px solid #313244;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
}
blockquote {
    border-left: 4px solid #89b4fa;
    margin: 0;
    padding-left: 14px;
    color: #bac2de;
}
ul, ol {
    padding-left: 20px;
}
li {
    margin-bottom: 4px;
}
</style>
"""
