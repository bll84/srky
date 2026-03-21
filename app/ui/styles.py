"""Application stylesheet."""

STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
}

QLabel {
    color: #cdd6f4;
    background: transparent;
}

QLabel#title {
    font-size: 20px;
    font-weight: bold;
    color: #89b4fa;
}

QLabel#subtitle {
    font-size: 11px;
    color: #a6adc8;
}

QLabel#sectionTitle {
    font-size: 15px;
    font-weight: bold;
    color: #cba6f7;
    padding: 4px 0px;
}

QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
}

QPushButton:pressed {
    background-color: #585b70;
}

QPushButton#primaryBtn {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    font-weight: bold;
}

QPushButton#primaryBtn:hover {
    background-color: #74c7ec;
}

QPushButton#dangerBtn {
    background-color: #f38ba8;
    color: #1e1e2e;
    border: none;
}

QPushButton#dangerBtn:hover {
    background-color: #eba0ac;
}

QPushButton:disabled {
    background-color: #313244;
    color: #585b70;
    border-color: #313244;
}

QTableWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    gridline-color: #313244;
    selection-background-color: #45475a;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #313244;
}

QHeaderView::section {
    background-color: #313244;
    color: #89b4fa;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #89b4fa;
    font-weight: bold;
}

QTextEdit, QPlainTextEdit {
    background-color: #181825;
    color: #a6e3a1;
    border: 1px solid #313244;
    border-radius: 6px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 12px;
    padding: 8px;
}

QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 12px;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
}

QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 12px;
}

QLineEdit:focus {
    border-color: #89b4fa;
}

QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #cdd6f4;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 4px;
}

QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 6px;
    background-color: #1e1e2e;
}

QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #89b4fa;
    border-bottom: 2px solid #89b4fa;
    background-color: #1e1e2e;
}

QTabBar::tab:hover {
    color: #cdd6f4;
    background-color: #313244;
}

QGroupBox {
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #cba6f7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QScrollBar:vertical {
    background-color: #181825;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QSplitter::handle {
    background-color: #313244;
    height: 2px;
}

QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
}
"""
