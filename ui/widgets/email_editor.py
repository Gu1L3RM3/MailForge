import uuid
import json
import os
from PySide6.QtCore import Slot, QObject, Signal, QUrl
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from core.resource_path import get_resource_path

# Objeto ponte para comunicação entre Python e JavaScript
class Bridge(QObject):
    # Sinais emitidos para a MainWindow
    componentSelected = Signal(dict)
    componentDeselected = Signal()
    requestImageUpload = Signal(str)  # Sinal para solicitar upload de imagem (recebe o component_id)
    property_changed = Signal(str, str, object)  # (component_id, property_name, new_value)

    @Slot(str)
    def on_component_selected(self, props_json):
        props = json.loads(props_json)
        self.componentSelected.emit(props)
        
    @Slot()
    def on_component_deselected(self):
        self.componentDeselected.emit()
        
    @Slot(str)
    def on_request_image_upload(self, component_id):
        self.requestImageUpload.emit(component_id)


class EmailEditor(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self.page_loaded = False
        self.loadFinished.connect(self._on_load_finished)

        # Configurar a ponte de comunicação
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("pyBridge", self.bridge)
        self.page().setWebChannel(self.channel)
        
        # Carregar o HTML base do editor usando o caminho de recurso
        template_path = get_resource_path(os.path.join('assets', 'editor_template.html'))
        self.load(QUrl.fromLocalFile(template_path))

    def _on_load_finished(self, ok):
        if ok:
            self.page_loaded = True

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and self.page_loaded:
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.page_loaded:
            return

        component_type = event.mimeData().text()
        component_id = f"comp-{uuid.uuid4().hex[:8]}"
        
        html_to_insert = self.get_html_for_component(component_type, component_id)
        
        if html_to_insert:
            js_code = f"""
            // Verificar se o drop foi feito dentro de uma coluna
            var dropTarget = document.elementFromPoint({event.position().x()}, {event.position().y()});
            var columnContainer = dropTarget.closest('.drop-column');
            
            // Adiciona o HTML no local apropriado
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = `{html_to_insert.strip()}`;
            var newComponent = tempDiv.firstChild;
            
            if (columnContainer) {{
                // Se for dentro de uma coluna, adiciona à coluna
                // Remover o texto placeholder se existir
                var placeholder = columnContainer.querySelector('.placeholder-text');
                if (placeholder) {{
                    placeholder.remove();
                }}
                columnContainer.appendChild(newComponent);
            }} else {{
                // Caso contrário, adiciona ao dropZone principal
                dropZone.appendChild(newComponent);
            }}
            """
            self.page().runJavaScript(js_code)
        
        event.acceptProposedAction()

    def get_html_for_component(self, component_type, component_id):
        if component_type == "text":
            return f'<div class="editable-component" data-id="{component_id}" data-type="text">Clique para editar este texto.</div>'
        elif component_type == "image":
            return f'<div style="text-align: left;"><img src="https://via.placeholder.com/600x150.png?text=Arraste+uma+imagem" alt="Imagem" class="editable-component" data-id="{component_id}" data-type="image"></div>'
        elif component_type == "button":
            return f'<div style="text-align: center;"><a href="#" class="editable-component" data-id="{component_id}" data-type="button" style="display:inline-block; padding: 12px 25px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">Botão Clicável</a></div>'
        elif component_type == "spacer":
            return f'<div class="editable-component" data-id="{component_id}" data-type="spacer" style="height: 20px; font-size: 1px;"> </div>'
        elif component_type == "divider":
            return f'<hr class="editable-component" data-id="{component_id}" data-type="divider" style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">'
        elif component_type == "two-columns":
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="two-columns" style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
                <div class="column drop-column" style="flex: 1; min-width: 200px; min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta coluna</div>
                </div>
                <div class="column drop-column" style="flex: 1; min-width: 200px; min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta coluna</div>
                </div>
            </div>
            '''
        elif component_type == "three-columns":
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="three-columns" style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
                <div class="column drop-column" style="flex: 1; min-width: 150px; min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta coluna</div>
                </div>
                <div class="column drop-column" style="flex: 1; min-width: 150px; min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta coluna</div>
                </div>
                <div class="column drop-column" style="flex: 1; min-width: 150px; min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta coluna</div>
                </div>
            </div>
            '''
        elif component_type == "two-rows":
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="two-rows" style="display: flex; flex-direction: column; gap: 20px; margin-bottom: 20px;">
                <div class="row drop-column" style="min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta linha</div>
                </div>
                <div class="row drop-column" style="min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta linha</div>
                </div>
            </div>
            '''
        elif component_type == "three-rows":
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="three-rows" style="display: flex; flex-direction: column; gap: 20px; margin-bottom: 20px;">
                <div class="row drop-column" style="min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta linha</div>
                </div>
                <div class="row drop-column" style="min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta linha</div>
                </div>
                <div class="row drop-column" style="min-height: 50px; border: 1px dashed #ccc; padding: 10px;">
                    <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para esta linha</div>
                </div>
            </div>
            '''
        elif component_type == "social":
            # Obter caminhos para os ícones de redes sociais
            facebook_icon = get_resource_path(os.path.join('assets', 'icons', 'facebook.png'))
            instagram_icon = get_resource_path(os.path.join('assets', 'icons', 'instagram.png'))
            twitter_icon = get_resource_path(os.path.join('assets', 'icons', 'twitter.png'))
            linkedin_icon = get_resource_path(os.path.join('assets', 'icons', 'linkedin.png'))
            youtube_icon = get_resource_path(os.path.join('assets', 'icons', 'youtube.png'))
            
            # Converter para URLs locais
            facebook_url = QUrl.fromLocalFile(facebook_icon).toString()
            instagram_url = QUrl.fromLocalFile(instagram_icon).toString()
            twitter_url = QUrl.fromLocalFile(twitter_icon).toString()
            linkedin_url = QUrl.fromLocalFile(linkedin_icon).toString()
            youtube_url = QUrl.fromLocalFile(youtube_icon).toString()
            
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="social" style="text-align: center; margin: 20px 0;">
                <a href="https://facebook.com" target="_blank" style="display: inline-block; margin: 0 10px;" class="social-icon" data-network="facebook">
                    <img src="{facebook_url}" width="32" height="32" alt="Facebook" style="border: none;">
                </a>
                <a href="https://instagram.com" target="_blank" style="display: inline-block; margin: 0 10px;" class="social-icon" data-network="instagram">
                    <img src="{instagram_url}" width="32" height="32" alt="Instagram" style="border: none;">
                </a>
                <a href="https://twitter.com" target="_blank" style="display: inline-block; margin: 0 10px;" class="social-icon" data-network="twitter">
                    <img src="{twitter_url}" width="32" height="32" alt="Twitter" style="border: none;">
                </a>
                <a href="https://linkedin.com" target="_blank" style="display: inline-block; margin: 0 10px;" class="social-icon" data-network="linkedin">
                    <img src="{linkedin_url}" width="32" height="32" alt="LinkedIn" style="border: none;">
                </a>
                <a href="https://youtube.com" target="_blank" style="display: inline-block; margin: 0 10px;" class="social-icon" data-network="youtube">
                    <img src="{youtube_url}" width="32" height="32" alt="YouTube" style="border: none;">
                </a>
            </div>
            '''
        elif component_type == "video":
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="video" style="margin: 20px 0; text-align: center;">
                <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
                    <img src="https://via.placeholder.com/600x338.png?text=Thumbnail+do+Video" alt="Thumbnail do vídeo" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; cursor: pointer;" data-video-url="https://www.youtube.com/embed/dQw4w9WgXcQ" class="video-thumbnail">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 68px; height: 48px; background-color: #ff0000; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                        <div style="width: 0; height: 0; border-style: solid; border-width: 10px 0 10px 20px; border-color: transparent transparent transparent #ffffff; margin-left: 5px;"></div>
                    </div>
                </div>
                <p style="margin-top: 10px; font-style: italic; color: #666;">Clique para editar o link do vídeo</p>
            </div>
            '''
        elif component_type == "html":
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="html" style="margin: 20px 0; border: 1px dashed #ccc; padding: 15px;">
                <div style="font-family: monospace; white-space: pre-wrap;"><!-- Insira seu código HTML personalizado aqui --></div>
            </div>
            '''
        return ""

    def update_component_property(self, component_id, prop, value):
        # Escapa aspas para não quebrar o JS
        if isinstance(value, str):
            value = value.replace('"', '\\"').replace('\n', '\\n').replace('`', '\\`')

        # Lógica especial para propriedades globais (sem component_id)
        if not component_id:
            if prop == "bgColor":
                # Altera diretamente o fundo do 'drop-zone'
                js_code = f"document.getElementById('drop-zone').style.backgroundColor = '{value}';"
                self.page().runJavaScript(js_code)
            # Se houver outras propriedades globais no futuro, podem ser adicionadas aqui
            return  # Sai da função após lidar com a propriedade global

        # A lógica para componentes específicos
        js_code = f"""
            var el = document.querySelector('[data-id="{component_id}"]');
            if (el) {{
        """
        
        # Propriedades de texto e botão
        if prop == "text":
            js_code += f'el.innerHTML = `{value}`;' # Usar backticks para multiline
        elif prop == "src" or prop == "href" or prop == "alt":
            js_code += f'el.{prop} = "{value}";'
        elif prop == "bgColor":
            # Corrigido: A propriedade bgColor no painel de propriedades do botão
            js_code += f'el.style.backgroundColor = "{value}";'
        elif prop == "height":
            js_code += f'el.style.height = "{value}";'
        elif prop == "color":
            # 'color' é para a cor do texto
            js_code += f'el.style.color = "{value}";'
        elif prop == "align":
            # Verifica se é um botão ou imagem e aplica o alinhamento ao elemento pai
            js_code += f'''
                if (el.dataset.type === "button" || (el.tagName === 'IMG' && el.parentElement.style.textAlign !== undefined)) {{
                    // Para botões e imagens, aplicamos o alinhamento ao elemento pai
                    var parentEl = el.parentElement;
                    if (parentEl) {{
                        parentEl.style.textAlign = "{value}";
                    }}
                }} else {{
                    // Para outros elementos (como texto), aplicamos diretamente
                    el.style.textAlign = "{value}";
                }}
            '''
        elif prop == "textColor":
            js_code += f'el.style.color = "{value}";'
        elif prop == "fontFamily":
            js_code += f'el.style.fontFamily = "{value}";'
        elif prop == "fontSize":
            js_code += f'el.style.fontSize = "{value}";'
        elif prop == "borderStyle":
            js_code += f'el.style.borderTopStyle = "{value}";'
        elif prop == "borderColor":
            js_code += f'el.style.borderTopColor = "{value}";'
        elif prop == "gap":
            js_code += f'el.style.gap = "{value}";'
        elif prop == "iconSize":
            js_code += f'''
                var imgs = el.querySelectorAll('img');
                for (var i = 0; i < imgs.length; i++) {{
                    imgs[i].setAttribute('width', "{value}");
                    imgs[i].setAttribute('height', "{value}");
                }}
            '''
        # Propriedades para mostrar/ocultar ícones de redes sociais
        elif prop.startswith("show"):
            js_code += f'''
                if (el.dataset.type === "social") {{
                    var network = "{prop[4:]}".toLowerCase();  // Extrai o nome da rede (ex: Facebook -> facebook)
                    var icon = el.querySelector('[data-network="' + network + '"]');
                    if (icon) {{
                        icon.style.display = "{"inline-block" if value else "none"}";
                    }}
                }}
            '''
        # Propriedades para links individuais de redes sociais
        elif prop.endswith("Link"):
            js_code += f'''
                if (el.dataset.type === "social") {{
                    var network = "{prop[:-4]}".toLowerCase();  // Extrai o nome da rede (ex: facebookLink -> facebook)
                    var icon = el.querySelector('[data-network="' + network + '"]');
                    if (icon) {{
                        icon.href = "{value}";
                    }}
                }}
            '''
        elif prop == "videoUrl":
            js_code += f'''
                // Atualiza o atributo data-video-url da thumbnail
                var thumbnail = el.querySelector('.video-thumbnail');
                if (thumbnail) {{
                    thumbnail.setAttribute('data-video-url', "{value}");
                }}
            '''
        elif prop == "thumbnailUrl":
            js_code += f'''
                // Atualiza a URL da thumbnail do vídeo
                var thumbnail = el.querySelector('.video-thumbnail');
                if (thumbnail) {{
                    thumbnail.src = "{value}";
                }}
            '''
        elif prop == "htmlContent":
            js_code += f'''
                // Atualiza o conteúdo HTML personalizado
                var contentDiv = el.querySelector('div');
                if (contentDiv) {{
                    contentDiv.innerHTML = `{value}`;
                }}
            '''
        
        js_code += "}"
        self.page().runJavaScript(js_code)
        
    def get_html_content(self, callback):
        # Usamos um callback porque a execução de JS é assíncrona
        js_code = "document.getElementById('drop-zone').innerHTML;"
        self.page().runJavaScript(js_code, 0, callback)

    def set_html_content(self, html):
        # Limpa o conteúdo atual e insere o novo
        js_code = f"""
        // Usando a variável global dropZone já declarada no template
        dropZone.innerHTML = `{html.replace('`', '\\`')}`;
        """
        self.page().runJavaScript(js_code)
        
    def delete_selected_component(self):
        # Chama a função JavaScript para excluir o componente selecionado
        js_code = "deleteSelectedComponent();"
        self.page().runJavaScript(js_code)
        
    def move_component_up(self):
        # Move o componente selecionado para cima
        js_code = "moveSelectedComponentUp();"
        self.page().runJavaScript(js_code)
        
    def move_component_down(self):
        # Move o componente selecionado para baixo
        js_code = "moveSelectedComponentDown();"
        self.page().runJavaScript(js_code)
        
    def upload_image(self, component_id):
        # Abre um diálogo para selecionar uma imagem do computador
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "", "Imagens (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            # Converte para URL local
            file_url = QUrl.fromLocalFile(file_path).toString()
            # Atualiza o componente com a nova imagem
            self.update_component_property(component_id, "src", file_url)