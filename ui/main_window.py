from PySide6.QtWidgets import (QMainWindow, QDockWidget, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction

from ui.widgets.component_palette import ComponentPalette
from ui.widgets.properties_panel import PropertiesPanel
from ui.widgets.email_editor import EmailEditor
from ui.dialogs.send_dialog import SendDialog
from ui.dialogs.config_dialog import ConfigDialog
from bs4 import BeautifulSoup
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MailForge - Editor Visual de Email")
        self.setGeometry(100, 100, 1400, 900)

        # 1. Editor Central
        self.editor = EmailEditor()
        self.setCentralWidget(self.editor)

        # 2. Paleta de Componentes (Esquerda)
        component_dock = QDockWidget("Componentes", self)
        self.component_palette = ComponentPalette()
        component_dock.setWidget(self.component_palette)
        self.addDockWidget(Qt.LeftDockWidgetArea, component_dock)

        # 3. Painel de Propriedades (Direita)
        properties_dock = QDockWidget("Propriedades", self)
        self.properties_panel = PropertiesPanel()
        properties_dock.setWidget(self.properties_panel)
        properties_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        properties_dock.setMinimumWidth(350)  # Largura mínima para garantir espaço suficiente
        properties_dock.setMinimumHeight(500)  # Altura mínima para garantir que os botões sejam visíveis
        self.addDockWidget(Qt.RightDockWidgetArea, properties_dock)

        # 4. Criar Ações e Menus
        self.create_actions()
        self.create_menus()
        
        # 5. Conectar Sinais e Slots
        self.editor.bridge.componentSelected.connect(self.properties_panel.display_properties)
        self.editor.bridge.componentDeselected.connect(self.properties_panel.clear_properties)
        self.editor.bridge.requestImageUpload.connect(self.editor.upload_image)
        self.properties_panel.property_changed.connect(self.editor.update_component_property)
        self.properties_panel.delete_component.connect(self.editor.delete_selected_component)
        self.properties_panel.move_component_up.connect(self.editor.move_component_up)
        self.properties_panel.move_component_down.connect(self.editor.move_component_down)
        self.properties_panel.upload_image.connect(self.editor.upload_image)

    def create_actions(self):
        self.open_action = QAction("&Abrir Template...", self, triggered=self.open_template)
        self.save_action = QAction("&Salvar Template...", self, triggered=self.save_template)
        self.send_action = QAction("&Enviar Email...", self, triggered=self.open_send_dialog)
        self.config_action = QAction("&Configurações de Email...", self, triggered=self.open_config_dialog)
        self.exit_action = QAction("S&air", self, triggered=self.close)

    def create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Arquivo")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        file_menu.addAction(self.send_action)
        file_menu.addAction(self.config_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
# Dentro da classe MainWindow em ui/main_window.py

    def _clean_html_for_sending(self, raw_html):
        """
        Usa BeautifulSoup para limpar o HTML do editor, preparando-o para envio.
        - Remove wrappers de componentes HTML.
        - Remove classes e atributos de dados específicos do editor.
        """
        soup = BeautifulSoup(raw_html, 'html.parser')

        # 1. Substitui os componentes de HTML customizado pelo seu conteúdo bruto
        for html_component in soup.find_all(attrs={"data-type": "html"}):
            # Pega o conteúdo interno do div e o substitui pelo wrapper
            inner_content = html_component.find('div')
            if inner_content:
                html_component.replace_with(BeautifulSoup(inner_content.decode_contents(), 'html.parser'))

        # 2. Remove classes e atributos de dados do editor de todos os elementos
        for tag in soup.find_all(True):
            if 'class' in tag.attrs:
                # Remove a classe 'editable-component' e 'selected'
                tag['class'] = [c for c in tag['class'] if c not in ['editable-component', 'selected']]
                if not tag['class']:
                    del tag['class'] # Remove o atributo se a lista de classes estiver vazia
            
            # Remove os atributos data-*
            for attr in list(tag.attrs.keys()):
                if attr.startswith('data-'):
                    del tag[attr]

        return str(soup)
    def open_template(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir Template", "", "Arquivos HTML (*.html *.htm)")
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                self.editor.set_html_content(html_content)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível carregar o template: {e}")

    def save_template(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Template", "", "Arquivos HTML (*.html)")
        if filepath:
            # A função get_html_content é assíncrona, então usamos um slot para receber o resultado
            self.editor.get_html_content(lambda html: self._write_html_to_file(filepath, html))

    def _write_html_to_file(self, filepath, html):
            try:
                # Limpa o HTML para remover artefatos do editor
                clean_html = self._clean_html_for_sending(html)
                
                # Cria um email final e bem formatado
                final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Seu Email</title>
    <style>
        body {{ margin: 0; padding: 0; background-color: #f4f4f4; }}
        table {{ border-collapse: collapse; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
    </head>
    <body>
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 600px;">
        <tr>
            <td style="padding: 20px; background-color: #ffffff;">
                {clean_html}
            </td>
        </tr>
    </table>
    </body>
    </html>
                """
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                QMessageBox.information(self, "Sucesso", "Template salvo com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar o template: {e}")
    def open_send_dialog(self):
        # Primeiro, obtemos o HTML atual do editor
        self.editor.get_html_content(self._get_bg_color_for_send_dialog)

    def _get_bg_color_for_send_dialog(self, html):
        if not html.strip():
            QMessageBox.warning(self, "Conteúdo Vazio", "O corpo do email está vazio. Adicione componentes antes de enviar.")
            return
            
        # Obtém a cor de fundo do editor
        self.editor.page().runJavaScript(
            "document.getElementById('drop-zone').style.backgroundColor;",
            0,
            lambda bg_color: self._show_send_dialog_with_html(html, bg_color)
        )

    @Slot(str)
    def _show_send_dialog_with_html(self, html, bg_color=None):
        if not bg_color or bg_color == "" or bg_color == "transparent":
            bg_color = "#ffffff"
            
        # Limpa o HTML antes de formatá-lo para envio
        clean_html = self._clean_html_for_sending(html)
        
        # Envolve o HTML com a cor de fundo apropriada
        formatted_html = f'<div style="background-color: {bg_color}; padding: 1px;">{clean_html}</div>'
        
        dialog = SendDialog(formatted_html, self)
        dialog.exec()
        
    def open_config_dialog(self):
        """Abre o diálogo de configurações de email"""
        dialog = ConfigDialog(self)
        dialog.exec()