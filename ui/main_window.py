# ui/main_window.py

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
        properties_dock.setMinimumWidth(350)
        properties_dock.setMinimumHeight(500)
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
        """Cria as ações para os menus com funcionalidades separadas."""
        self.open_project_action = QAction("&Abrir Projeto...", self, triggered=self.open_project)
        self.save_project_action = QAction("&Salvar Projeto...", self, triggered=self.save_project)
        self.export_html_action = QAction("E&xportar para HTML...", self, triggered=self.export_as_html)
        self.send_action = QAction("&Enviar Email...", self, triggered=self.open_send_dialog)
        self.config_action = QAction("&Configurações de Email...", self, triggered=self.open_config_dialog)
        self.exit_action = QAction("S&air", self, triggered=self.close)

    def create_menus(self):
        """Cria e popula os menus da aplicação."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Arquivo")
        file_menu.addAction(self.open_project_action)
        file_menu.addAction(self.save_project_action)
        file_menu.addAction(self.export_html_action)
        file_menu.addSeparator()
        file_menu.addAction(self.send_action)
        file_menu.addAction(self.config_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

    def open_project(self):
        """Abre um arquivo de projeto (.mf) que contém o HTML bruto do editor."""
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir Projeto MailForge", "", "Projetos MailForge (*.mf)")
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                self.editor.set_html_content(html_content)
                QMessageBox.information(self, "Projeto Carregado", "O projeto foi carregado com sucesso e está pronto para edição.")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Abrir", f"Não foi possível carregar o projeto: {e}")

    def save_project(self):
        """Salva o estado atual do editor em um arquivo de projeto (.mf)."""
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar Projeto MailForge", "", "Projetos MailForge (*.mf)")
        if filepath:
            if not filepath.lower().endswith('.mf'):
                filepath += '.mf'
            self.editor.get_html_content(lambda html: self._write_raw_html_to_file(filepath, html))

    def _write_raw_html_to_file(self, filepath, raw_html):
        """Escreve o HTML bruto do editor em um arquivo, preservando todos os dados de edição."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(raw_html)
            QMessageBox.information(self, "Projeto Salvo", "Seu projeto foi salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o projeto: {e}")

    def export_as_html(self):
        """Exporta o design atual como um arquivo HTML final, limpo e compatível com email."""
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar para HTML", "", "Arquivos HTML (*.html *.htm)")
        if filepath:
            self.editor.get_html_content(lambda html: self._write_clean_html_to_file(filepath, html))

    def _write_clean_html_to_file(self, filepath, raw_html):
        """Limpa o HTML e o envolve em um boilerplate padrão antes de salvar."""
        try:
            clean_html = self._clean_html_for_sending(raw_html)
            final_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Seu Email</title>
<style>
    body {{ margin: 0; padding: 0; background-color: #f4f4f4; }}
    table {{ border-collapse: collapse; mso-table-lspace:0pt; mso-table-rspace:0pt; }}
    img {{ max-width: 100%; height: auto; display: block; }}
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
</html>"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_html)
            QMessageBox.information(self, "Sucesso", "HTML exportado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", f"Não foi possível exportar o HTML: {e}")

    
    def _clean_html_for_sending(self,raw_html):
        """
        Converte o HTML do editor em um formato compatível com email, usando tabelas.
        Trata corretamente botões, redes sociais, bordas curvadas e alinhamento de textos.
        """
        if not raw_html:
            return ""

        soup = BeautifulSoup(raw_html, 'html.parser')

        # ETAPA 1: CONVERTER COLUNAS EM TABELAS
        for columns_container in soup.find_all(attrs={"data-type": ["two-columns", "three-columns"]}):
            inner_cols = columns_container.find_all(class_="column", recursive=False)
            if not inner_cols:
                continue
            num_cols = len(inner_cols)
            col_width = f"{100 / num_cols:.2f}%"
            gap_match = re.search(r'gap:\s*(\d+)px', columns_container.get('style', ''))
            padding_val = int(gap_match.group(1)) // 2 if gap_match else 10

            layout_table = soup.new_tag('table', role="presentation", border="0", cellpadding="0", cellspacing="0", width="100%")
            tr = soup.new_tag('tr')
            layout_table.append(tr)

            for i, col_div in enumerate(inner_cols):
                td = soup.new_tag('td', width=col_width, valign="top")
                padding_style = []
                if i > 0: padding_style.append(f"padding-left: {padding_val}px")
                if i < num_cols - 1: padding_style.append(f"padding-right: {padding_val}px")
                if padding_style: td['style'] = '; '.join(padding_style)
                td.extend(list(col_div.children))
                tr.append(td)
            columns_container.replace_with(layout_table)

        # ETAPA 2: CONVERTER COMPONENTES
        for component in soup.find_all(class_="editable-component"):
            if component.find_parent('td'):
                continue

            component_type = component.get('data-type', '')
            align = component.get('data-align', 'left')
            styles = {k.strip(): v.strip() for k, v in (s.split(':', 1) for s in component.get('style', '').split(';') if ':' in s)}

            wrapper_table = soup.new_tag('table', role="presentation", border="0", cellpadding="0", cellspacing="0", width="100%")
            tr = soup.new_tag('tr')
            td = soup.new_tag('td')
            tr.append(td)
            wrapper_table.append(tr)

            td['align'] = align
            td_style = []

            # Preserva alinhamento vertical para centralização real
            if align == "center":
                td['valign'] = 'middle'
                td_style.append("text-align: center; vertical-align: middle;")
            else:
                td_style.append(f"text-align: {align};")

            # Copia estilos importantes
            for prop in ['background-color', 'font-family', 'font-size', 'color', 'height', 'width']:
                if prop in styles:
                    td_style.append(f"{prop}: {styles[prop]}")

            # Borda arredondada
            def extract_border_radius(styles):
                radius_props = [
                    'border-radius',
                    'border-top-left-radius',
                    'border-top-right-radius',
                    'border-bottom-left-radius',
                    'border-bottom-right-radius'
                ]
                return [f"{prop}: {styles[prop]}" for prop in radius_props if prop in styles and styles[prop] != '0px']

            td_style.extend(extract_border_radius(styles))
            td['style'] = '; '.join(td_style)

            if component_type == 'button':
                a_tag = component.find('a')
                if not a_tag:
                    continue
                a_styles = {k.strip(): v.strip() for k, v in (s.split(':', 1) for s in a_tag.get('style', '').split(';') if ':' in s)}

                # Recompor estilo inline para botão
                a_tag['style'] = (
                    f"display: inline-block; text-decoration: none; "
                    f"padding: {a_styles.get('padding', '12px 25px')}; "
                    f"font-family: {a_styles.get('font-family', 'Arial, sans-serif')}; "
                    f"font-size: {a_styles.get('font-size', '16px')}; "
                    f"font-weight: {a_styles.get('font-weight', 'bold')}; "
                    f"color: {a_styles.get('color', '#ffffff')}; "
                    f"background-color: {a_styles.get('background-color', '#3498db')}; "
                    f"border-radius: {a_styles.get('border-radius', '5px')};"
                )
                td.append(a_tag)

            else:
                td.extend(list(component.children))

            component.replace_with(wrapper_table)

        # ETAPA 3: LIMPEZA FINAL
        for tag in soup.find_all(True):
            # Remover atributos data-* e id
            attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('data-') or attr == 'id']
            for attr in attrs_to_remove:
                del tag[attr]

            # Limpeza de classes
            if 'class' in tag.attrs:
                classes_to_keep = [c for c in tag['class'] if c not in ['editable-component', 'selected', 'drop-column', 'column', 'row', 'placeholder-text', 'drag-over', 'text-content']]
                if classes_to_keep:
                    tag['class'] = classes_to_keep
                else:
                    del tag['class']

            # Limpeza e preservação de estilo útil
            if 'style' in tag.attrs:
                style = tag['style']
                for pattern in [
                    r'min-height:[^;]+;?',
                    r'display:\s*flex;?',
                    r'justify-content:[^;]+;?',
                    r'align-items:[^;]+;?',
                    r'flex-direction:[^;]+;?',
                    r'border-style:\s*dashed;?'
                ]:
                    style = re.sub(pattern, '', style, flags=re.IGNORECASE).strip()
                tag['style'] = style.strip(';').strip() if style else None
                if tag['style'] is None:
                    del tag['style']
        return soup.body.decode_contents() if soup.body else str(soup)

    # --- CORREÇÃO APLICADA AQUI ---
    @Slot()
    def open_send_dialog(self):
        self.editor.get_html_content(self._get_bg_color_for_send_dialog)
    
    def _get_bg_color_for_send_dialog(self, html):
        if not html.strip():
            QMessageBox.warning(self, "Conteúdo Vazio", "O corpo do email está vazio.")
            return
        self.editor.page().runJavaScript(
            "document.getElementById('drop-zone').style.backgroundColor;",
            0,
            lambda bg_color: self._show_send_dialog_with_html(html, bg_color)
        )

    # Nota: Este método não precisa ser um slot, pois é chamado diretamente pelo Python.
    def _show_send_dialog_with_html(self, html, bg_color=None):
        if not bg_color or bg_color == "" or bg_color == "transparent":
            bg_color = "#ffffff"
        clean_html = self._clean_html_for_sending(html)
        
        formatted_html = f'''
        <div style="background-color: {bg_color}; padding: 1px;">
            <style type="text/css">
                table[align="center"] {{ margin-left: auto; margin-right: auto; }}
                table[align="right"] {{ margin-left: auto; }}
                td[align="center"] {{ text-align: center !important; }}
                td[align="right"] {{ text-align: right !important; }}
                td[align="left"] {{ text-align: left !important; }}
                a {{ text-decoration: none; }}
                a[href] {{ color: inherit; }}
                img {{ border: 0; display: block; }}
                .button {{ display: inline-block; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: inherit; }}
                a[data-type="button"] {{ 
                    display: inline-block !important; padding: 12px 25px !important; text-decoration: none !important; 
                    font-weight: bold !important; background-color: #3498db !important; color: white !important; 
                    border-radius: 5px !important; text-align: center !important;
                    mso-padding-alt: 12px 25px !important; mso-line-height-rule: exactly !important;
                }}
                hr {{ border: 0; border-top: 1px solid #ccc; margin: 20px 0; }}
                .spacer {{ font-size: 1px; line-height: 1px; }}
                * {{ -webkit-text-size-adjust: none; }}
                a, span, p, div {{ font-size: inherit; }}
            </style>
            {clean_html}
        </div>'''
        
        dialog = SendDialog(formatted_html, self)
        dialog.exec()
        
    def open_config_dialog(self):
        dialog = ConfigDialog(self)
        dialog.exec()