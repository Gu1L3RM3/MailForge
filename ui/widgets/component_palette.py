from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt
from core.resource_path import get_resource_path
import os

class ComponentPalette(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setIconSize(QSize(48, 48))
        self.setSpacing(10)
        self.setDropIndicatorShown(False)
        self.setGridSize(QSize(60, 60))

        self.add_component("Texto", "text", "assets/icons/text.png")
        self.add_component("Imagem", "image", "assets/icons/image.png")
        self.add_component("Botão", "button", "assets/icons/button.png")
        self.add_component("Espaçador", "spacer", "assets/icons/spacer.png")
        self.add_component("Divisor", "divider", "assets/icons/divider.png")
        self.add_component("Centralizador", "center", "assets/icons/center.png")
        self.add_component("Duas Colunas", "two-columns", "assets/icons/two-columns.png")
        self.add_component("Três Colunas", "three-columns", "assets/icons/three-columns.png")
        self.add_component("Duas Linhas", "two-rows", "assets/icons/two-rows.png")
        self.add_component("Três Linhas", "three-rows", "assets/icons/three-rows.png")
        self.add_component("Redes Sociais", "social", "assets/icons/social.png")
        self.add_component("Vídeo", "video", "assets/icons/video.png")
        self.add_component("HTML", "html", "assets/icons/code.png")

    def add_component(self, name, type_id, icon_path):
        # Usar get_resource_path para obter o caminho absoluto do ícone
        absolute_icon_path = get_resource_path(icon_path)
        item = QListWidgetItem(QIcon(absolute_icon_path), "")
        item.setData(Qt.UserRole, type_id) # Usamos UserRole para guardar o tipo
        item.setSizeHint(QSize(60, 60))
        item.setTextAlignment(Qt.AlignCenter)
        self.addItem(item)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            mime_data = self.model().mimeData([self.indexFromItem(item)])
            # O texto do MimeData será o tipo do componente
            mime_data.setText(item.data(Qt.UserRole))
            
            from PySide6.QtGui import QDrag
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(supportedActions)