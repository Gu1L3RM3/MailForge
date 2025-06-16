import uuid
import json
import os
import html
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
    requestImageUpload = Signal(str)
    property_changed = Signal(str, str, object)

    # --- CORREÇÃO APLICADA AQUI ---
    # Adicione o decorador @Slot() aos métodos que são chamados pelo JavaScript.
    # O argumento 'str' informa ao Qt que este slot espera uma string.
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
            return f'''<div class="editable-component" data-id="{component_id}" data-type="text" style="height: 50px;">
                        <span class="text-content">Clique para editar este texto.</span>
                    </div>'''
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
            tiktok_icon = get_resource_path(os.path.join('assets', 'icons', 'tiktok.png'))
            
            # Converter para URLs locais
            facebook_url = QUrl.fromLocalFile(facebook_icon).toString()
            instagram_url = QUrl.fromLocalFile(instagram_icon).toString()
            twitter_url = QUrl.fromLocalFile(twitter_icon).toString()
            linkedin_url = QUrl.fromLocalFile(linkedin_icon).toString()
            youtube_url = QUrl.fromLocalFile(youtube_icon).toString()
            tiktok_url = QUrl.fromLocalFile(tiktok_icon).toString()
            
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
                <a href="https://tiktok.com" target="_blank" style="display: inline-block; margin: 0 10px;" class="social-icon" data-network="tiktok">
                    <img src="{tiktok_url}" width="32" height="32" alt="TikTok" style="border: none;">
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
        elif component_type == "center":
            return f'''
            <div class="editable-component drop-column" data-id="{component_id}" data-type="center" style="display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 15px; border: 1px solid transparent; background-color: transparent; width: 100%; height: 100%; min-height: 50px; box-sizing: border-box;">
                <div class="placeholder-text" style="color: #999; font-style: italic;">Arraste componentes para centralizar</div>
            </div>
            '''
        elif component_type == "html":
            initial_code = "<!-- Insira seu código HTML personalizado aqui -->"
            escaped_code = html.escape(initial_code,quote=True)
            return f'''
            <div class="editable-component" data-id="{component_id}" data-type="html" 
                 data-raw-html="{escaped_code}" 
                 style="margin: 20px 0; border: 1px dashed #ccc; padding: 15px;">
                <div class="html-content-view" style="font-family: monospace; white-space: pre-wrap;">{initial_code}</div>
            </div>
            '''
        return ""

    # Dentro da classe EmailEditor em ui/widgets/email_editor.py

    def update_component_property(self, component_id, prop, value):
        # --- LÓGICA DE ESCAPE UNIFICADA ---
        # Prepara o valor para ser injetado de forma segura no código JavaScript.
        # Usa template literals (`) como o método padrão para strings.
        js_value = ""
        if isinstance(value, str):
            # Escapa os caracteres que conflitam com template literals do JS:
            # ` (acento grave), \ (barra invertida) e ${ (interpolação).
            js_value = value.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
            # Coloca o valor dentro dos acentos graves para formar uma string JS.
            js_value_str = f"`{js_value}`"
        elif isinstance(value, bool):
            # Converte booleano Python para string JS (true/false).
            js_value_str = str(value).lower()
        else:
            # Para números e outros tipos, json.dumps é seguro.
            import json
            js_value_str = json.dumps(value)

        # --- LÓGICA PARA PROPRIEDADES GLOBAIS ---
        if not component_id:
            if prop == "bgColor":
                js_code = f"document.getElementById('drop-zone').style.backgroundColor = {js_value_str};"
                self.page().runJavaScript(js_code)
            return

        # --- LÓGICA PARA COMPONENTES ESPECÍFICOS ---
        js_code = f"""
            var el = document.querySelector('[data-id="{component_id}"]');
            if (el) {{
        """

        if prop == "text":
            js_code += f'''
            // Verifica se é um botão ou um componente de texto
            if (el.dataset.type === 'button') {{
                // Para botões, atualiza o innerText diretamente
                el.innerText = {js_value_str};
            }} else {{
                // Para outros componentes de texto, procura pelo elemento .text-content
                var content = el.querySelector('.text-content');
                if (content) {{
                    content.innerHTML = {js_value_str};
                }}
            }}
        '''
        elif prop in ["src", "href", "alt"]:
            js_code += f'el.{prop} = {js_value_str};'
        elif prop == "bgColor":
            js_code += f'el.style.backgroundColor = {js_value_str};'
        elif prop == "height":
            js_code += f'el.style.height = {js_value_str};'
        elif prop == "width":
            # Para imagens, o atributo 'width' também deve ser atualizado.
            js_code += f'''
                el.style.width = {js_value_str};
                if (el.tagName === 'IMG') {{
                    el.width = String({js_value_str}).replace("px", "");
                }}
            '''
        elif prop == "color" or prop == "textColor":
            js_code += f'el.style.color = {js_value_str};'
        # CÓDIGO NOVO E CORRIGIDO (dentro de update_component_property)
        elif prop == "align":
            js_code += f'''
        // Tratamento especial para componente de texto para permitir centralização vertical
        if (el.dataset.type === 'text') {{
            if ({js_value_str} === 'center') {{
                // Aplica Flexbox para centralização visual no *editor*
                el.style.display = 'flex';
                el.style.justifyContent = 'center';
                el.style.alignItems = 'center';
                el.style.textAlign = 'center';
            }} else {{
                // Reverte para o comportamento padrão
                el.style.display = 'block'; // 'block' é o padrão para <div>
                el.style.justifyContent = '';
                el.style.alignItems = '';
                el.style.textAlign = {js_value_str};
            }}
            // Adiciona o atributo data-align para que a exportação saiba o que fazer
            el.setAttribute('data-align', {js_value_str});
        }}
        // Lógica para outros componentes que são alinhados pelo seu contêiner pai
        else if (el.dataset.type === "button" || el.dataset.type === "social" || (el.tagName === 'IMG' && el.parentElement)) {{
            var parentEl = el.parentElement;
            if (parentEl) {{
                parentEl.style.textAlign = {js_value_str};
                parentEl.setAttribute('data-align', {js_value_str});
            }}
        }}
        // Fallback
        else {{
            el.style.textAlign = {js_value_str};
            el.setAttribute('data-align', {js_value_str});
        }}
    '''
        elif prop == "fontFamily":
            js_code += f'el.style.fontFamily = {js_value_str};'
        elif prop == "fontSize":
            js_code += f'el.style.fontSize = {js_value_str};'
        elif prop == "borderStyle":
            js_code += f'el.style.borderTopStyle = {js_value_str};'
        elif prop == "borderColor":
            js_code += f'el.style.borderTopColor = {js_value_str};'
        elif prop == "borderWidth":
            js_code += f'el.style.borderTopWidth = {js_value_str};'
        elif prop == "gap":
            js_code += f'el.style.gap = {js_value_str};'
        elif prop == "iconSize":
            js_code += f'''
                el.querySelectorAll('img').forEach(img => {{
                    img.setAttribute('width', {js_value_str});
                    img.setAttribute('height', {js_value_str});
                }});
            '''
        elif prop.startswith("show"):
            network = prop[4:].lower()
            js_code += f'''
                var icon = el.querySelector('[data-network="{network}"]');
                if (icon) {{
                    icon.style.display = {js_value_str} ? "inline-block" : "none";
                }}
            '''
        elif prop.endswith("Link"):
            network = prop[:-4].lower()
            js_code += f'''
                var icon = el.querySelector('[data-network="{network}"]');
                if (icon) {{ icon.href = {js_value_str}; }}
            '''
        elif prop == "borderRadius":
            js_code += f'el.style.borderRadius = "{value}";'
        elif prop == "borderRadiusTopLeft":
            js_code += f'el.style.borderTopLeftRadius = "{value}";'
        elif prop == "borderRadiusTopRight":
            js_code += f'el.style.borderTopRightRadius = "{value}";'
        elif prop == "borderRadiusBottomLeft":
            js_code += f'el.style.borderBottomLeftRadius = "{value}";'
        elif prop == "borderRadiusBottomRight":
            js_code += f'el.style.borderBottomRightRadius = "{value}";'
        elif prop == "backgroundColor":
            js_code += f'el.style.backgroundColor = {js_value_str};'
        elif prop == "videoUrl":
            js_code += f'''
                var thumbnail = el.querySelector('.video-thumbnail');
                if (thumbnail) {{ thumbnail.setAttribute('data-video-url', {js_value_str}); }}
            '''
        elif prop == "thumbnailUrl":
            js_code += f'''
                var thumbnail = el.querySelector('.video-thumbnail');
                if (thumbnail) {{ thumbnail.src = {js_value_str}; }}
            '''
        elif prop == "htmlContent":
            # Lógica corrigida para o componente HTML
            js_code += f'''
                // 1. Atualiza o atributo 'data-raw-html' (fonte da verdade) com o código-fonte.
                el.dataset.rawHtml = {js_value_str};
                
                // 2. Atualiza a div interna para a visualização.
                var contentDiv = el.querySelector('.html-content-view');
                if (contentDiv) {{
                    contentDiv.innerHTML = {js_value_str};
                }}
            '''
        
        js_code += "}"
        self.page().runJavaScript(js_code)
        
    def get_html_content(self, callback):
        # Usamos um callback porque a execução de JS é assíncrona
        js_code = "document.getElementById('drop-zone').innerHTML;"
        self.page().runJavaScript(js_code, 0, callback)



    def set_html_content(self, html):
        """
        Limpa o conteúdo atual do editor e insere o novo HTML de um projeto.
        Em seguida, re-anexa os listeners de eventos aos componentes.
        """
        # Escapa o HTML para ser inserido de forma segura em uma template literal do JS
        js_html = html.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

        js_code = f"""
        // 1. Injeta o HTML do projeto no editor.
        dropZone.innerHTML = `{js_html}`;

        // 2. Re-anexa o listener de clique a todos os componentes existentes.
        // O event.currentTarget garante que estamos selecionando o elemento que tem o listener.
        document.querySelectorAll('.editable-component').forEach(component => {{
            component.addEventListener('click', (event) => {{
                // Prevenir navegação para links durante a edição
                if (event.target.tagName === 'A' || event.target.closest('a')) {{
                    event.preventDefault();
                }}
                
                // A lógica de seleção é chamada aqui.
                // Isso evita o problema de múltiplos listeners.
                const clickedComponent = event.currentTarget;
                
                if (selectedComponent) {{
                    selectedComponent.classList.remove('selected');
                }}

                if (clickedComponent) {{
                    clickedComponent.classList.add('selected');
                    selectedComponent = clickedComponent;

                    // Coleta as propriedades como antes
                    const props = {{
                        id: clickedComponent.dataset.id,
                        type: clickedComponent.dataset.type,
                        align: clickedComponent.style.textAlign || 'left',
                        borderRadius: clickedComponent.style.borderRadius || '0px',
                        width: clickedComponent.style.width || '',
                        height: clickedComponent.style.height || ''
                        // Adicione outras propriedades comuns se necessário
                    }};
                    
                    if (props.type === 'html') {{
                        props.htmlContent = clickedComponent.dataset.rawHtml || '';
                    }} else if (props.type === 'text') {{
                        props.text = clickedComponent.innerHTML;
                    }}
                    // Adicione outras lógicas de coleta de 'props' aqui...

                    pyBridge.on_component_selected(JSON.stringify(props));
                }}
                event.stopPropagation();
            }});
        }});

        // 3. Reativa as zonas de drop para os layouts de colunas/linhas
        setupDropColumns();
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