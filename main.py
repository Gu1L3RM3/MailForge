# main.py
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow
from core.resource_path import get_resource_path

if __name__ == "__main__":
    # Garante que os caminhos relativos para assets funcionem
    # independentemente de onde o script é executado
    try:
        # Se estiver em um executável PyInstaller
        base_path = sys._MEIPASS
        os.chdir(base_path)
    except Exception:
        # Se não estiver em um executável, usa o diretório do script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = QApplication(sys.argv)

    # Definir o ícone do aplicativo usando get_resource_path
    icon_path = get_resource_path(os.path.join('assets', 'app_icon.ico'))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print("Aviso: Ícone do aplicativo não encontrado em", icon_path)

    # Carregar a folha de estilos usando get_resource_path
    try:
        style_path = get_resource_path(os.path.join('styles', 'style.qss'))
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Aviso: Arquivo de estilo não encontrado. A aplicação usará o estilo padrão.")

    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())