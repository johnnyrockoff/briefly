#!/usr/bin/env python3
import os
import signal
import sys
from pathlib import Path

# Adiciona o diretório base ao sys.path para importações relativas e absolutas limpas
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.styles import DARK_THEME_QSS


def main():
    # Permite que o Python capture Ctrl+C no terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Configuração de alta densidade de pixels (HiDPI)
    QCoreApplication.setApplicationName("Briefly")
    QCoreApplication.setOrganizationName("Briefly")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Mantém o app vivo na bandeja do sistema!
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
