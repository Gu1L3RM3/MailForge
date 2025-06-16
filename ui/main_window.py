from PySide6.QtWidgets import (QMainWindow, QDockWidget, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
import re
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






    def _clean_html_for_sending(self, raw_html):
        """
        Converte o HTML do editor em um formato compatível com email, processando
        layouts de coluna/linha e componentes individuais em tabelas aninhadas.
        """
        if not raw_html:
            return ""

        soup = BeautifulSoup(raw_html, 'html.parser')

        # ETAPA 1: CONVERTER LAYOUTS DE COLUNAS E LINHAS EM TABELAS
        # Esta etapa é executada primeiro para construir a estrutura principal.
        
        # Lida com componentes de colunas (lado a lado)
        for columns_container in soup.find_all(attrs={"data-type": ["two-columns", "three-columns"]}):
            inner_cols = columns_container.find_all(class_="column", recursive=False)
            if not inner_cols:
                continue

            num_cols = len(inner_cols)
            col_width = f"{100 / num_cols:.2f}%"
            
            # Extrai o espaçamento (gap) para converter em padding
            gap_style = columns_container.get('style', '')
            gap_match = re.search(r'gap:\s*(\d+)px', gap_style)
            padding_val = int(gap_match.group(1)) // 2 if gap_match else 10

            # Cria a tabela de layout
            layout_table = soup.new_tag('table', role="presentation", border="0", cellpadding="0", cellspacing="0", width="100%")
            tr = soup.new_tag('tr')
            layout_table.append(tr)

            for i, col_div in enumerate(inner_cols):
                td = soup.new_tag('td', width=col_width, valign="top")
                
                # Simula o 'gap' com 'padding'
                padding_style = f"padding-left: {padding_val}px; padding-right: {padding_val}px;"
                # Adiciona padding esquerdo apenas se não for a primeira coluna
                if i == 0: padding_style = f"padding-right: {padding_val}px;"
                # Adiciona padding direito apenas se não for a última coluna
                if i == num_cols -1: padding_style = f"padding-left: {padding_val}px;"

                td['style'] = padding_style
                
                # Move o conteúdo da coluna div para a nova célula td
                td.extend(list(col_div.children))
                tr.append(td)
            
            columns_container.replace_with(layout_table)

        # Lida com componentes de linhas (empilhadas)
        for rows_container in soup.find_all(attrs={"data-type": ["two-rows", "three-rows"]}):
            inner_rows = rows_container.find_all(class_="row", recursive=False)
            if not inner_rows:
                continue
            
            # Cria a tabela de layout
            layout_table = soup.new_tag('table', role="presentation", border="0", cellpadding="0", cellspacing="0", width="100%")

            for row_div in inner_rows:
                tr = soup.new_tag('tr')
                td = soup.new_tag('td', valign="top")
                
                # Move o conteúdo da linha div para a nova célula td
                td.extend(list(row_div.children))
                tr.append(td)
                layout_table.append(tr)
            
            rows_container.replace_with(layout_table)
            
        # ETAPA 2: PROCESSAR COMPONENTES SIMPLES (TEXTO, IMAGEM, BOTÃO, ETC.)
        # Agora que os layouts são tabelas, processamos o conteúdo dentro deles.
        # Envolvemos componentes com tamanho/fundo/alinhamento em suas próprias tabelas.
        
        # Usamos uma lista para evitar modificar a árvore enquanto iteramos sobre ela
        components_to_process = soup.find_all('div', class_="editable-component")
        for component in components_to_process:
            style_string = component.get('style', '')
            if not style_string:
                continue

            styles = {k.strip(): v.strip() for k, v in (s.split(':', 1) for s in style_string.split(';') if ':' in s)}
            
            width = styles.get('width')
            height = styles.get('height')
            align = styles.get('text-align', 'left')
            bg_color = styles.get('background-color')
            padding = styles.get('padding', '5px')
            border_radius = styles.get('border-radius')
            font_color = styles.get('color')
            font_size = styles.get('font-size')
            font_family = styles.get('font-family')
            
            # Cria a tabela para o componente individual
            wrapper_table = soup.new_tag('table', role="presentation", border="0", cellpadding="0", cellspacing="0")
            if width and '%' not in width:
                wrapper_table['width'] = re.sub(r'px$', '', width)
            else:
                wrapper_table['width'] = "100%"

            tr = soup.new_tag('tr')
            td = soup.new_tag('td')
            wrapper_table.append(tr)
            tr.append(td)

            # Monta os estilos para o <td>
            td_styles = []
            if width: td_styles.append(f"width: {width}")
            if height: td_styles.append(f"height: {height}")
            if bg_color: td_styles.append(f"background-color: {bg_color}")
            if padding: td_styles.append(f"padding: {padding}")
            if border_radius: td_styles.append(f"border-radius: {border_radius}")
            if font_color: td_styles.append(f"color: {font_color}")
            if font_size: td_styles.append(f"font-size: {font_size}")
            if font_family: td_styles.append(f"font-family: {font_family}")

            td['align'] = align
            if td_styles:
                td['style'] = '; '.join(td_styles)

            # Move o conteúdo do div para o td
            td.extend(list(component.children))
            component.replace_with(wrapper_table)

        # ETAPA 3: LIMPEZA FINAL
        # Remove quaisquer classes, atributos e estilos restantes do editor.
        for tag in soup.find_all(True):
            # Remove atributos data-* e id
            attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('data-') or attr == 'id']
            for attr in attrs_to_remove:
                del tag[attr]

            # Remove classes do editor
            if 'class' in tag.attrs:
                classes_to_keep = [c for c in tag['class'] if c not in [
                    'editable-component', 'selected', 'drop-column', 'column', 'row',
                    'placeholder-text', 'drag-over'
                ]]
                if classes_to_keep:
                    tag['class'] = classes_to_keep
                else:
                    del tag['class']
            
            # Remove estilos restantes do editor
            if 'style' in tag.attrs:
                style = tag['style']
                style = re.sub(r'border:\s*1px\s+dashed\s+[^;]+;?', '', style, flags=re.IGNORECASE).strip()
                style = re.sub(r'min-height:[^;]+;?', '', style).strip()
                if style:
                    tag['style'] = style.strip(';')
                else:
                    del tag['style']

        return soup.body.decode_contents() if soup.body else str(soup)
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