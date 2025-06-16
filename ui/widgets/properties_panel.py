from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel, 
                             QLineEdit, QPushButton, QFormLayout, QColorDialog, QSpinBox)
from PySide6.QtGui import QColor, QPalette, QTextCursor
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTextEdit,QCheckBox,QGroupBox

class PropertiesPanel(QWidget):
    # Sinais emitidos
    property_changed = Signal(str, str, object)  # (component_id, property_name, new_value)
    delete_component = Signal()  # Solicita exclusão do componente selecionado
    move_component_up = Signal()  # Solicita mover componente para cima
    move_component_down = Signal()  # Solicita mover componente para baixo
    upload_image = Signal(str)  # Solicita upload de imagem (component_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_component_id = None
        self.current_component_type = None

        self.main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        
        # Botão de cor de fundo do email
        self.bg_color_btn = QPushButton("Cor de Fundo do Email")
        self.bg_color_btn.clicked.connect(self.pick_bg_color)
        self.bg_color_btn.setStyleSheet("background-color: blue; color: white;")
        self.main_layout.addWidget(self.bg_color_btn)
        
        # Criar controles de estilo comuns para todos os componentes
        self.style_controls = QWidget()
        self.style_layout = QFormLayout(self.style_controls)
        
        # Controle de bordas arredondadas
        self.border_radius_group = QGroupBox("Bordas Arredondadas")
        self.border_radius_layout = QVBoxLayout(self.border_radius_group)
        
        # Opções de tipo de borda
        self.border_type_layout = QHBoxLayout()
        self.border_square = QPushButton("Quadradas")
        self.border_rounded = QPushButton("Arredondadas")
        self.border_square.clicked.connect(lambda: self.set_border_radius("0px"))
        self.border_rounded.clicked.connect(lambda: self.show_border_radius_controls())
        self.border_type_layout.addWidget(self.border_square)
        self.border_type_layout.addWidget(self.border_rounded)
        self.border_radius_layout.addLayout(self.border_type_layout)
        
        # Controles individuais para cada canto
        self.corner_controls = QWidget()
        self.corner_layout = QFormLayout(self.corner_controls)
        
        # Controle para todos os cantos
        self.all_corners_layout = QHBoxLayout()
        self.all_corners_label = QLabel("Todos os cantos:")
        self.all_corners_spin = QSpinBox()
        self.all_corners_spin.setRange(0, 50)
        self.all_corners_spin.setSuffix(" px")
        self.all_corners_spin.valueChanged.connect(self.update_all_corners)
        self.all_corners_layout.addWidget(self.all_corners_label)
        self.all_corners_layout.addWidget(self.all_corners_spin)
        self.corner_layout.addRow(self.all_corners_layout)
        
        # Controles para cantos individuais
        self.top_left_spin = QSpinBox()
        self.top_left_spin.setRange(0, 50)
        self.top_left_spin.setSuffix(" px")
        self.top_left_spin.valueChanged.connect(lambda v: self.emit_change("borderRadiusTopLeft", f"{v}px"))
        
        self.top_right_spin = QSpinBox()
        self.top_right_spin.setRange(0, 50)
        self.top_right_spin.setSuffix(" px")
        self.top_right_spin.valueChanged.connect(lambda v: self.emit_change("borderRadiusTopRight", f"{v}px"))
        
        self.bottom_left_spin = QSpinBox()
        self.bottom_left_spin.setRange(0, 50)
        self.bottom_left_spin.setSuffix(" px")
        self.bottom_left_spin.valueChanged.connect(lambda v: self.emit_change("borderRadiusBottomLeft", f"{v}px"))
        
        self.bottom_right_spin = QSpinBox()
        self.bottom_right_spin.setRange(0, 50)
        self.bottom_right_spin.setSuffix(" px")
        self.bottom_right_spin.valueChanged.connect(lambda v: self.emit_change("borderRadiusBottomRight", f"{v}px"))
        
        self.corner_layout.addRow("Superior Esquerdo:", self.top_left_spin)
        self.corner_layout.addRow("Superior Direito:", self.top_right_spin)
        self.corner_layout.addRow("Inferior Esquerdo:", self.bottom_left_spin)
        self.corner_layout.addRow("Inferior Direito:", self.bottom_right_spin)
        
        # Inicialmente oculta os controles de cantos individuais
        self.corner_controls.setVisible(False)
        self.border_radius_layout.addWidget(self.corner_controls)
        
        self.style_layout.addRow(self.border_radius_group)
        
        # Inicialmente oculta os controles de estilo
        self.style_controls.setVisible(False)
        self.main_layout.addWidget(self.style_controls)
        
        # Página 0: Vazio (quando nada está selecionado)
        self.empty_widget = QLabel("Selecione um componente para editar suas propriedades.")
        self.empty_widget.setWordWrap(True)
        self.stacked_widget.addWidget(self.empty_widget)
        
        # Página 1: Propriedades de Texto
        self.text_props = QWidget()
        self.text_layout = QFormLayout(self.text_props)
        
        # Substituir QLineEdit por QTextEdit para permitir expansão automática
        
        self.text_content_edit = QTextEdit()
        self.text_content_edit.setMinimumHeight(80)
        self.text_content_edit.setAcceptRichText(False)
        self.text_content_edit.textChanged.connect(lambda: self.emit_change("text", self.text_content_edit.toPlainText()))
        
        # Configurar para expandir automaticamente
        self.text_content_edit.document().contentsChanged.connect(self.adjust_text_edit_height)
        
        self.text_layout.addRow("Conteúdo:", self.text_content_edit)
        
        # Adicionar controles de tamanho para texto
        self.text_size_group = QGroupBox("Tamanho do Componente")
        self.text_size_layout = QFormLayout(self.text_size_group)
        
        # Controle de largura
        self.text_width_spin = QSpinBox()
        self.text_width_spin.setRange(10, 1000)
        self.text_width_spin.setSuffix(" px")
        self.text_width_spin.setValue(600)
        self.text_width_spin.valueChanged.connect(lambda w: self.emit_change("width", f"{w}px"))
        self.text_size_layout.addRow("Largura:", self.text_width_spin)
        
        # Controle de altura
        self.text_height_spin = QSpinBox()
        self.text_height_spin.setRange(10, 1000)
        self.text_height_spin.setSuffix(" px")
        self.text_height_spin.setValue(150)
        self.text_height_spin.valueChanged.connect(lambda h: self.emit_change("height", f"{h}px"))
        self.text_size_layout.addRow("Altura:", self.text_height_spin)
        
        # Adicionar opções de alinhamento
        self.text_align_layout = QVBoxLayout()
        self.text_align_left = QPushButton("Esquerda")
        self.text_align_center = QPushButton("Centro")
        self.text_align_right = QPushButton("Direita")
        self.text_align_justify = QPushButton("Justificado")
        
        self.text_align_left.clicked.connect(lambda: self.emit_change("align", "left"))
        self.text_align_center.clicked.connect(lambda: self.emit_change("align", "center"))
        self.text_align_right.clicked.connect(lambda: self.emit_change("align", "right"))
        self.text_align_justify.clicked.connect(lambda: self.emit_change("align", "justify"))
        
        self.text_align_layout.addWidget(self.text_align_left)
        self.text_align_layout.addWidget(self.text_align_center)
        self.text_align_layout.addWidget(self.text_align_right)
        self.text_align_layout.addWidget(self.text_align_justify)
        
        # Adicionar botão de cor do texto
        self.text_color_btn = QPushButton("Cor do Texto")
        self.text_color_btn.clicked.connect(self.pick_text_color)
        
        # Adicionar seletor de fonte
        self.font_layout = QHBoxLayout()
        self.font_arial = QPushButton("Arial")
        self.font_times = QPushButton("Times New Roman")
        self.font_verdana = QPushButton("Verdana")
        self.font_custom = QPushButton("Fonte Personalizada")
        
        self.font_arial.clicked.connect(lambda: self.emit_change("fontFamily", "Arial, sans-serif"))
        self.font_times.clicked.connect(lambda: self.emit_change("fontFamily", "'Times New Roman', serif"))
        self.font_verdana.clicked.connect(lambda: self.emit_change("fontFamily", "Verdana, sans-serif"))
        self.font_custom.clicked.connect(self.load_custom_font)
        
        self.font_layout.addWidget(self.font_arial)
        self.font_layout.addWidget(self.font_times)
        self.font_layout.addWidget(self.font_verdana)
        self.font_layout.addWidget(self.font_custom)
        
        # Adicionar controle de tamanho de fonte
        self.font_size_layout = QHBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setSuffix(" px")
        self.font_size_spin.setValue(16)
        self.font_size_spin.valueChanged.connect(lambda s: self.emit_change("fontSize", f"{s}px"))
        
        self.font_size_layout.addWidget(self.font_size_spin)
        
        # Botão de cor de fundo para o componente de texto
        self.text_bg_color_btn = QPushButton("Cor de Fundo")
        self.text_bg_color_btn.clicked.connect(self.pick_component_bg_color)
        self.text_bg_color_btn.setStyleSheet("background-color: blue; color: white;")
        
        self.text_layout.addRow("Alinhamento:", self.text_align_layout)
        self.text_layout.addRow("Fonte:", self.font_layout)
        self.text_layout.addRow("Tamanho da Fonte:", self.font_size_layout)
        self.text_layout.addRow(self.text_color_btn)
        self.text_layout.addRow(self.text_bg_color_btn)
        self.text_layout.addRow(self.text_size_group)
        self.stacked_widget.addWidget(self.text_props)

        # Página 2: Propriedades de Imagem
        self.image_props = QWidget()
        self.image_layout = QFormLayout(self.image_props)
        self.image_src_edit = QLineEdit()
        self.image_src_edit.textChanged.connect(lambda t: self.emit_change("src", t))
        self.image_alt_edit = QLineEdit()
        self.image_alt_edit.textChanged.connect(lambda t: self.emit_change("alt", t))
        self.upload_image_btn = QPushButton("Carregar Imagem do Computador")
        self.upload_image_btn.clicked.connect(self.request_image_upload)
        
        # Adicionar controles de tamanho para imagem
        self.image_size_group = QGroupBox("Tamanho da Imagem")
        self.image_size_layout = QFormLayout(self.image_size_group)
        
        # Controle de largura
        self.image_width_spin = QSpinBox()
        self.image_width_spin.setRange(10, 1000)
        self.image_width_spin.setSuffix(" px")
        self.image_width_spin.setValue(600)
        self.image_width_spin.valueChanged.connect(lambda w: self.emit_change("width", f"{w}px"))
        self.image_size_layout.addRow("Largura:", self.image_width_spin)
        
        # Controle de altura
        self.image_height_spin = QSpinBox()
        self.image_height_spin.setRange(10, 1000)
        self.image_height_spin.setSuffix(" px")
        self.image_height_spin.setValue(150)
        self.image_height_spin.valueChanged.connect(lambda h: self.emit_change("height", f"{h}px"))
        self.image_size_layout.addRow("Altura:", self.image_height_spin)
        
        # Checkbox para manter proporção
        self.image_keep_ratio = QCheckBox("Manter proporção")
        self.image_keep_ratio.setChecked(True)
        self.image_size_layout.addRow(self.image_keep_ratio)
        
        # Adicionar opções de alinhamento para imagem
        self.image_align_layout = QVBoxLayout()
        self.image_align_left = QPushButton("Esquerda")
        self.image_align_center = QPushButton("Centro")
        self.image_align_right = QPushButton("Direita")
        
        self.image_align_left.clicked.connect(lambda: self.emit_change("align", "left"))
        self.image_align_center.clicked.connect(lambda: self.emit_change("align", "center"))
        self.image_align_right.clicked.connect(lambda: self.emit_change("align", "right"))
        
        self.image_align_layout.addWidget(self.image_align_left)
        self.image_align_layout.addWidget(self.image_align_center)
        self.image_align_layout.addWidget(self.image_align_right)
        
        # Botão de cor de fundo para o componente de imagem
        self.image_bg_color_btn = QPushButton("Cor de Fundo")
        self.image_bg_color_btn.clicked.connect(self.pick_component_bg_color)
        self.image_bg_color_btn.setStyleSheet("background-color: blue; color: white;")
        
        self.image_layout.addRow("URL da Imagem:", self.image_src_edit)
        self.image_layout.addRow("Texto Alternativo:", self.image_alt_edit)
        self.image_layout.addRow(self.image_size_group)
        self.image_layout.addRow("Alinhamento:", self.image_align_layout)
        self.image_layout.addRow(self.upload_image_btn)
        self.image_layout.addRow(self.image_bg_color_btn)
        self.stacked_widget.addWidget(self.image_props)

        # Página 3: Propriedades de Botão
        self.button_props = QWidget()
        self.button_layout = QFormLayout(self.button_props)
        self.button_text_edit = QLineEdit()
        self.button_text_edit.textChanged.connect(lambda t: self.emit_change("text", t))
        self.button_href_edit = QLineEdit()
        self.button_href_edit.textChanged.connect(lambda t: self.emit_change("href", t))
        self.button_color_btn = QPushButton("Cor de Fundo")
        self.button_color_btn.clicked.connect(self.pick_button_color)
        self.button_color_btn.setStyleSheet("background-color: blue; color: white;")
        self.button_text_color_btn = QPushButton("Cor do Texto")
        self.button_text_color_btn.clicked.connect(self.pick_button_text_color)
        
        # Adicionar controle de tamanho de fonte para botão
        self.button_font_size_layout = QHBoxLayout()
        self.button_font_size_spin = QSpinBox()
        self.button_font_size_spin.setRange(8, 72)
        self.button_font_size_spin.setSuffix(" px")
        self.button_font_size_spin.setValue(16)
        self.button_font_size_spin.valueChanged.connect(lambda s: self.emit_change("fontSize", f"{s}px"))
        
        self.button_font_size_layout.addWidget(self.button_font_size_spin)
        
        # Adicionar opções de alinhamento para botão
        self.button_align_layout = QVBoxLayout()
        self.button_align_left = QPushButton("Esquerda")
        self.button_align_center = QPushButton("Centro")
        self.button_align_right = QPushButton("Direita")
        
        self.button_align_left.clicked.connect(lambda: self.emit_change("align", "left"))
        self.button_align_center.clicked.connect(lambda: self.emit_change("align", "center"))
        self.button_align_right.clicked.connect(lambda: self.emit_change("align", "right"))
        
        self.button_align_layout.addWidget(self.button_align_left)
        self.button_align_layout.addWidget(self.button_align_center)
        self.button_align_layout.addWidget(self.button_align_right)
        
        # Adicionar seletor de fonte para botão
        self.button_font_layout = QHBoxLayout()
        self.button_font_arial = QPushButton("Arial")
        self.button_font_times = QPushButton("Times New Roman")
        self.button_font_verdana = QPushButton("Verdana")
        self.button_font_custom = QPushButton("Fonte Personalizada")
        
        self.button_font_arial.clicked.connect(lambda: self.emit_change("fontFamily", "Arial, sans-serif"))
        self.button_font_times.clicked.connect(lambda: self.emit_change("fontFamily", "'Times New Roman', serif"))
        self.button_font_verdana.clicked.connect(lambda: self.emit_change("fontFamily", "Verdana, sans-serif"))
        self.button_font_custom.clicked.connect(self.load_custom_font_button)
        
        self.button_font_layout.addWidget(self.button_font_arial)
        self.button_font_layout.addWidget(self.button_font_times)
        self.button_font_layout.addWidget(self.button_font_verdana)
        self.button_font_layout.addWidget(self.button_font_custom)
        
        # Adicionar controles de tamanho para botão
        self.button_size_group = QGroupBox("Tamanho do Botão")
        self.button_size_layout = QFormLayout(self.button_size_group)
        
        # Controle de largura
        self.button_width_spin = QSpinBox()
        self.button_width_spin.setRange(10, 1000)
        self.button_width_spin.setSuffix(" px")
        self.button_width_spin.setValue(200)
        self.button_width_spin.valueChanged.connect(lambda w: self.emit_change("width", f"{w}px"))
        self.button_size_layout.addRow("Largura:", self.button_width_spin)
        
        # Controle de altura
        self.button_height_spin = QSpinBox()
        self.button_height_spin.setRange(10, 1000)
        self.button_height_spin.setSuffix(" px")
        self.button_height_spin.setValue(40)
        self.button_height_spin.valueChanged.connect(lambda h: self.emit_change("height", f"{h}px"))
        self.button_size_layout.addRow("Altura:", self.button_height_spin)
        
        self.button_layout.addRow("Texto do Botão:", self.button_text_edit)
        self.button_layout.addRow("URL do Link:", self.button_href_edit)
        self.button_layout.addRow("Alinhamento:", self.button_align_layout)
        self.button_layout.addRow("Fonte:", self.button_font_layout)
        self.button_layout.addRow("Tamanho da Fonte:", self.button_font_size_layout)
        self.button_layout.addRow(self.button_color_btn)
        self.button_layout.addRow(self.button_text_color_btn)
        self.button_layout.addRow(self.button_size_group)
        self.stacked_widget.addWidget(self.button_props)

        # Página 4: Propriedades do Espaçador
        self.spacer_props = QWidget()
        self.spacer_layout = QFormLayout(self.spacer_props)
        self.spacer_height_spin = QSpinBox()
        self.spacer_height_spin.setRange(10, 500)
        self.spacer_height_spin.setSuffix(" px")
        self.spacer_height_spin.valueChanged.connect(lambda h: self.emit_change("height", f"{h}px"))
        self.spacer_layout.addRow("Altura:", self.spacer_height_spin)
        self.stacked_widget.addWidget(self.spacer_props)

        # Página 5: Propriedades do Divisor
        self.divider_props = QWidget()
        self.divider_layout = QFormLayout(self.divider_props)
        self.divider_color_btn = QPushButton("Cor do Divisor")
        self.divider_color_btn.clicked.connect(self.pick_divider_color)
        self.divider_style_layout = QHBoxLayout()
        self.divider_solid = QPushButton("Sólido")
        self.divider_dashed = QPushButton("Tracejado")
        self.divider_dotted = QPushButton("Pontilhado")
        self.divider_solid.clicked.connect(lambda: self.emit_change("borderStyle", "solid"))
        self.divider_dashed.clicked.connect(lambda: self.emit_change("borderStyle", "dashed"))
        self.divider_dotted.clicked.connect(lambda: self.emit_change("borderStyle", "dotted"))
        self.divider_style_layout.addWidget(self.divider_solid)
        self.divider_style_layout.addWidget(self.divider_dashed)
        self.divider_style_layout.addWidget(self.divider_dotted)
        
        # Controle de espessura do divisor
        self.divider_thickness_layout = QHBoxLayout()
        self.divider_thickness_label = QLabel("Espessura:")
        self.divider_thickness_spin = QSpinBox()
        self.divider_thickness_spin.setRange(1, 10)
        self.divider_thickness_spin.setSuffix(" px")
        self.divider_thickness_spin.setValue(1)
        self.divider_thickness_spin.valueChanged.connect(lambda t: self.emit_change("borderWidth", f"{t}px"))
        self.divider_thickness_layout.addWidget(self.divider_thickness_label)
        self.divider_thickness_layout.addWidget(self.divider_thickness_spin)
        
        self.divider_layout.addRow("Estilo:", self.divider_style_layout)
        self.divider_layout.addRow(self.divider_thickness_layout)
        self.divider_layout.addRow(self.divider_color_btn)
        self.stacked_widget.addWidget(self.divider_props)
        
        # Página 6: Propriedades de Colunas e Center
        self.columns_props = QWidget()
        self.columns_layout = QFormLayout(self.columns_props)
        
        # Propriedades específicas para colunas
        self.columns_group = QGroupBox("Propriedades de Colunas")
        self.columns_group_layout = QFormLayout(self.columns_group)
        self.columns_gap_spin = QSpinBox()
        self.columns_gap_spin.setRange(0, 100)
        self.columns_gap_spin.setSuffix(" px")
        self.columns_gap_spin.setValue(20)
        self.columns_gap_spin.valueChanged.connect(lambda g: self.emit_change("gap", f"{g}px"))
        self.columns_group_layout.addRow("Espaçamento entre colunas:", self.columns_gap_spin)
        
        # Propriedades específicas para o componente center
        self.center_group = QGroupBox("Propriedades do Centralizador")
        self.center_group_layout = QFormLayout(self.center_group)
        
        # Botão de cor de fundo para o componente center
        self.center_bg_color_btn = QPushButton("Cor de Fundo")
        self.center_bg_color_btn.clicked.connect(self.pick_component_bg_color)
        self.center_bg_color_btn.setStyleSheet("background-color: blue; color: white;")
        self.center_group_layout.addRow(self.center_bg_color_btn)
        
        # Adiciona os grupos ao layout principal
        self.columns_layout.addRow(self.columns_group)
        self.columns_layout.addRow(self.center_group)
        
        self.stacked_widget.addWidget(self.columns_props)
        
        # Página 7: Propriedades de Redes Sociais
        self.social_props = QWidget()
        self.social_layout = QFormLayout(self.social_props)
        
        # Tamanho dos ícones
        self.social_size_spin = QSpinBox()
        self.social_size_spin.setRange(16, 64)
        self.social_size_spin.setSuffix(" px")
        self.social_size_spin.setValue(32)
        self.social_size_spin.valueChanged.connect(lambda s: self.emit_change("iconSize", f"{s}px"))
        self.social_layout.addRow("Tamanho dos ícones:", self.social_size_spin)
        
        # Opções de alinhamento para redes sociais
        self.social_align_layout = QVBoxLayout()
        self.social_align_left = QPushButton("Esquerda")
        self.social_align_center = QPushButton("Centro")
        self.social_align_right = QPushButton("Direita")
        self.social_align_left.clicked.connect(lambda: self.emit_change("align", "left"))
        self.social_align_center.clicked.connect(lambda: self.emit_change("align", "center"))
        self.social_align_right.clicked.connect(lambda: self.emit_change("align", "right"))
        self.social_align_layout.addWidget(self.social_align_left)
        self.social_align_layout.addWidget(self.social_align_center)
        self.social_align_layout.addWidget(self.social_align_right)
        self.social_layout.addRow("Alinhamento:", self.social_align_layout)
        
        # Checkboxes para escolher quais redes sociais exibir
        
        self.social_networks_group = QGroupBox("Redes Sociais a Exibir")
        self.social_networks_layout = QVBoxLayout()
        
        self.facebook_check = QCheckBox("Facebook")
        self.instagram_check = QCheckBox("Instagram")
        self.twitter_check = QCheckBox("Twitter")
        self.linkedin_check = QCheckBox("LinkedIn")
        self.youtube_check = QCheckBox("YouTube")
        self.tiktok_check = QCheckBox("TikTok")
        
        self.facebook_check.setChecked(True)
        self.instagram_check.setChecked(True)
        self.twitter_check.setChecked(True)
        self.linkedin_check.setChecked(True)
        self.youtube_check.setChecked(True)
        self.tiktok_check.setChecked(True)
        
        self.facebook_check.stateChanged.connect(lambda state: self.emit_change("showFacebook", bool(state)))
        self.instagram_check.stateChanged.connect(lambda state: self.emit_change("showInstagram", bool(state)))
        self.twitter_check.stateChanged.connect(lambda state: self.emit_change("showTwitter", bool(state)))
        self.linkedin_check.stateChanged.connect(lambda state: self.emit_change("showLinkedin", bool(state)))
        self.youtube_check.stateChanged.connect(lambda state: self.emit_change("showYoutube", bool(state)))
        self.tiktok_check.stateChanged.connect(lambda state: self.emit_change("showTiktok", bool(state)))
        
        self.social_networks_layout.addWidget(self.facebook_check)
        self.social_networks_layout.addWidget(self.instagram_check)
        self.social_networks_layout.addWidget(self.twitter_check)
        self.social_networks_layout.addWidget(self.linkedin_check)
        self.social_networks_layout.addWidget(self.youtube_check)
        self.social_networks_layout.addWidget(self.tiktok_check)
        
        self.social_networks_group.setLayout(self.social_networks_layout)
        self.social_layout.addRow(self.social_networks_group)
        
        # Links individuais para cada rede social
        self.social_links_group = QGroupBox("Links das Redes Sociais")
        self.social_links_layout = QFormLayout()
        
        self.facebook_link = QLineEdit("https://facebook.com")
        self.instagram_link = QLineEdit("https://instagram.com")
        self.twitter_link = QLineEdit("https://twitter.com")
        self.linkedin_link = QLineEdit("https://linkedin.com")
        self.youtube_link = QLineEdit("https://youtube.com")
        self.tiktok_link = QLineEdit("https://tiktok.com")
        
        self.facebook_link.textChanged.connect(lambda t: self.emit_change("facebookLink", t))
        self.instagram_link.textChanged.connect(lambda t: self.emit_change("instagramLink", t))
        self.twitter_link.textChanged.connect(lambda t: self.emit_change("twitterLink", t))
        self.linkedin_link.textChanged.connect(lambda t: self.emit_change("linkedinLink", t))
        self.youtube_link.textChanged.connect(lambda t: self.emit_change("youtubeLink", t))
        self.tiktok_link.textChanged.connect(lambda t: self.emit_change("tiktokLink", t))
        
        self.social_links_layout.addRow("Facebook:", self.facebook_link)
        self.social_links_layout.addRow("Instagram:", self.instagram_link)
        self.social_links_layout.addRow("Twitter:", self.twitter_link)
        self.social_links_layout.addRow("LinkedIn:", self.linkedin_link)
        self.social_links_layout.addRow("YouTube:", self.youtube_link)
        self.social_links_layout.addRow("TikTok:", self.tiktok_link)
        
        self.social_links_group.setLayout(self.social_links_layout)
        self.social_layout.addRow(self.social_links_group)
        self.stacked_widget.addWidget(self.social_props)
        
        # Página 8: Propriedades de Vídeo
        self.video_props = QWidget()
        self.video_layout = QFormLayout(self.video_props)
        self.video_url_edit = QLineEdit()
        self.video_url_edit.textChanged.connect(lambda t: self.emit_change("videoUrl", t))
        self.video_thumbnail_edit = QLineEdit()
        self.video_thumbnail_edit.textChanged.connect(lambda t: self.emit_change("thumbnailUrl", t))
        self.video_upload_thumbnail_btn = QPushButton("Carregar Thumbnail")
        self.video_upload_thumbnail_btn.clicked.connect(self.request_video_thumbnail_upload)
        self.video_layout.addRow("URL do Vídeo:", self.video_url_edit)
        self.video_layout.addRow("URL da Thumbnail:", self.video_thumbnail_edit)
        self.video_layout.addRow(self.video_upload_thumbnail_btn)
        self.stacked_widget.addWidget(self.video_props)
        
        # Página 9: Propriedades de HTML
        self.html_props = QWidget()
        self.html_layout = QFormLayout(self.html_props)
        self.html_content_edit = QTextEdit() # Usando QTextEdit para ter mais espaço
        self.html_content_edit.setMinimumHeight(500)  # Aumentando ainda mais a altura mínima
        self.html_content_edit.setMinimumWidth(350)   # Definindo uma largura mínima
        self.html_content_edit.setStyleSheet("font-family: 'Courier New', monospace; font-size: 12px;") # Melhorando a legibilidade
        
        # Configurando uma fonte monoespaçada para melhor visualização do código
        from PySide6.QtGui import QFont
        code_font = QFont("Courier New", 10)
        self.html_content_edit.setFont(code_font)
        
        self.html_content_edit.textChanged.connect(lambda: self.emit_change("htmlContent", self.html_content_edit.toPlainText()))
        
        # Adicionando botões para formatação básica de HTML
        format_layout = QHBoxLayout()
        bold_btn = QPushButton("<b>B</b>")
        italic_btn = QPushButton("<i>I</i>")
        link_btn = QPushButton("Link")
        paragraph_btn = QPushButton("<p>")
        
        bold_btn.clicked.connect(lambda: self.insert_html_tag("<b>", "</b>"))
        italic_btn.clicked.connect(lambda: self.insert_html_tag("<i>", "</i>"))
        link_btn.clicked.connect(lambda: self.insert_html_tag('<a href="#">', "</a>"))
        paragraph_btn.clicked.connect(lambda: self.insert_html_tag("<p>", "</p>"))
        
        format_layout.addWidget(bold_btn)
        format_layout.addWidget(italic_btn)
        format_layout.addWidget(link_btn)
        format_layout.addWidget(paragraph_btn)
        
        self.html_layout.addRow("Formatação:", format_layout)
        self.html_layout.addRow("Código HTML:", self.html_content_edit)
        self.stacked_widget.addWidget(self.html_props)
        
        # Mapeia tipo de componente para o índice do widget no stack
        self.type_map = {
            "text": 1,
            "image": 2,
            "button": 3,
            "spacer": 4,
            "divider": 5,
            "two-columns": 6,
            "three-columns": 6,
            "social": 7,
            "video": 8,
            "html": 9,
            "center": 6
        }
        
        # Adicionar controles de componente (excluir, mover para cima/baixo)
        self.component_controls = QWidget()
        self.component_controls.setVisible(False)  # Inicialmente oculto
        self.component_controls.setMinimumHeight(50)  # Altura mínima para garantir visibilidade
        self.controls_layout = QHBoxLayout(self.component_controls)
        self.controls_layout.setContentsMargins(5, 5, 5, 5)  # Margens reduzidas
        
        self.delete_btn = QPushButton("Excluir")
        self.delete_btn.clicked.connect(self.request_delete)
        self.delete_btn.setMinimumHeight(40)  # Altura mínima para o botão
        self.delete_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        
        self.move_up_btn = QPushButton("↑ Mover para Cima")
        self.move_up_btn.clicked.connect(self.request_move_up)
        self.move_up_btn.setMinimumHeight(40)  # Altura mínima para o botão
        self.move_up_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        
        self.move_down_btn = QPushButton("↓ Mover para Baixo")
        self.move_down_btn.clicked.connect(self.request_move_down)
        self.move_down_btn.setMinimumHeight(40)  # Altura mínima para o botão
        self.move_down_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        
        self.controls_layout.addWidget(self.delete_btn)
        self.controls_layout.addWidget(self.move_up_btn)
        self.controls_layout.addWidget(self.move_down_btn)
        
        # Criar um QScrollArea para o conteúdo principal
        from PySide6.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.stacked_widget)
        
        # Adiciona um espaçador para empurrar os controles para o final do layout
        self.main_layout.addWidget(self.scroll_area, 1)  # Stretch factor 1
        
        # Adiciona um widget fixo para os controles de componente
        self.controls_container = QWidget()
        self.controls_container.setMinimumHeight(60)  # Altura fixa para garantir visibilidade
        self.controls_container.setMaximumHeight(60)  # Altura máxima para não ocupar muito espaço
        self.controls_container_layout = QVBoxLayout(self.controls_container)
        self.controls_container_layout.setContentsMargins(5, 5, 5, 5)
        self.controls_container_layout.addWidget(self.component_controls)
        
        # Adiciona o container de controles ao layout principal
        self.main_layout.addWidget(self.controls_container, 0)  # Sem stretch
        self.stacked_widget.setCurrentIndex(0) # Começa vazio

    def display_properties(self, props):
        self.current_component_id = props['id']
        self.current_component_type = props['type']
        
        # Desconecta sinais para não emitir durante o preenchimento
        self.blockSignals(True)
        
        widget_index = self.type_map.get(self.current_component_type, 0)
        self.stacked_widget.setCurrentIndex(widget_index)
        
        # Mostra os controles de componente
        self.component_controls.setVisible(True)
        
        # Mostra os controles de estilo comuns
        self.style_controls.setVisible(True)
        
        # Carrega as propriedades de estilo
        bg_color = props.get('backgroundColor', '')
        
        # Não alteramos mais a cor de fundo dos botões para manter consistência visual
        # A cor de fundo do componente é tratada internamente sem alterar a aparência dos botões
            
        # Carrega as propriedades de borda
        border_radius = props.get('borderRadius', '0px')
        if border_radius != '0px':
            # Se tiver borda arredondada, mostra os controles individuais
            self.corner_controls.setVisible(True)
            
            # Tenta extrair o valor numérico
            try:
                radius_value = int(border_radius.replace('px', ''))
                self.all_corners_spin.setValue(radius_value)
            except (ValueError, AttributeError):
                self.all_corners_spin.setValue(0)
                
            # Carrega valores individuais para cada canto
            top_left = props.get('borderRadiusTopLeft', border_radius)
            top_right = props.get('borderRadiusTopRight', border_radius)
            bottom_left = props.get('borderRadiusBottomLeft', border_radius)
            bottom_right = props.get('borderRadiusBottomRight', border_radius)
            
            try:
                self.top_left_spin.setValue(int(top_left.replace('px', '')))
                self.top_right_spin.setValue(int(top_right.replace('px', '')))
                self.bottom_left_spin.setValue(int(bottom_left.replace('px', '')))
                self.bottom_right_spin.setValue(int(bottom_right.replace('px', '')))
            except (ValueError, AttributeError):
                pass
        else:
            # Se não tiver borda arredondada, oculta os controles individuais
            self.corner_controls.setVisible(False)
            self.all_corners_spin.setValue(0)

        if self.current_component_type == "text":
            self.text_content_edit.setText(props.get('text', ''))
            # Atualizar cor do texto
            color = QColor(props.get('color', '#333'))
            self.text_color_btn.setStyleSheet(f"color: {color.name()};")
            
            # Destacar o botão de alinhamento ativo
            align = props.get('align', 'left')
            self.text_align_left.setStyleSheet("font-weight: normal;")
            self.text_align_center.setStyleSheet("font-weight: normal;")
            self.text_align_right.setStyleSheet("font-weight: normal;")
            self.text_align_justify.setStyleSheet("font-weight: normal;")
            
            if align == 'left':
                self.text_align_left.setStyleSheet("font-weight: bold;")
            elif align == 'center':
                self.text_align_center.setStyleSheet("font-weight: bold;")
            elif align == 'right':
                self.text_align_right.setStyleSheet("font-weight: bold;")
            elif align == 'justify':
                self.text_align_justify.setStyleSheet("font-weight: bold;")
                
            # Atualizar tamanho da fonte
            font_size = props.get('fontSize', '16px')
            if font_size:
                try:
                    size_value = int(font_size.replace('px', ''))
                    self.font_size_spin.setValue(size_value)
                except (ValueError, AttributeError):
                    self.font_size_spin.setValue(16)
        elif self.current_component_type == "image":
            self.image_src_edit.setText(props.get('src', ''))
            self.image_alt_edit.setText(props.get('alt', ''))
            
            # Carregar valores de largura e altura
            width = props.get('width', '600px')
            height = props.get('height', '150px')
            
            # Extrair valores numéricos
            try:
                width_value = int(width.replace('px', ''))
                self.image_width_spin.setValue(width_value)
            except (ValueError, AttributeError):
                self.image_width_spin.setValue(600)
                
            try:
                height_value = int(height.replace('px', ''))
                self.image_height_spin.setValue(height_value)
            except (ValueError, AttributeError):
                self.image_height_spin.setValue(150)
            
            # Destacar o botão de alinhamento ativo para imagens
            align = props.get('align', 'left')
            self.image_align_left.setStyleSheet("font-weight: normal;")
            self.image_align_center.setStyleSheet("font-weight: normal;")
            self.image_align_right.setStyleSheet("font-weight: normal;")
            
            if align == 'left':
                self.image_align_left.setStyleSheet("font-weight: bold;")
            elif align == 'center':
                self.image_align_center.setStyleSheet("font-weight: bold;")
            elif align == 'right':
                self.image_align_right.setStyleSheet("font-weight: bold;")
        elif self.current_component_type == "button":
            self.button_text_edit.setText(props.get('text', ''))
            self.button_href_edit.setText(props.get('href', '#'))
            color = QColor(props.get('bgColor', '#3498db'))
            self.button_color_btn.setStyleSheet(f"background-color: {color.name()};")
            
            # Atualizar tamanho da fonte do botão
            font_size = props.get('fontSize', '16px')
            if font_size:
                try:
                    size_value = int(font_size.replace('px', ''))
                    self.button_font_size_spin.setValue(size_value)
                except (ValueError, AttributeError):
                    self.button_font_size_spin.setValue(16)
                    
            # Carregar valores de largura e altura para o componente de botão
            width = props.get('width', '')
            height = props.get('height', '')
            
            if width:
                try:
                    width_value = int(width.replace('px', ''))
                    self.button_width_spin.setValue(width_value)
                except (ValueError, AttributeError):
                    self.button_width_spin.setValue(200)
            
            if height:
                try:
                    height_value = int(height.replace('px', ''))
                    self.button_height_spin.setValue(height_value)
                except (ValueError, AttributeError):
                    self.button_height_spin.setValue(40)
        elif self.current_component_type == "spacer":
            height = int(props.get('height', '20px').replace('px', ''))
            self.spacer_height_spin.setValue(height)
        elif self.current_component_type == "divider":
            # Destacar o botão de estilo ativo
            style = props.get('borderStyle', 'solid')
            self.divider_solid.setStyleSheet("font-weight: normal;")
            self.divider_dashed.setStyleSheet("font-weight: normal;")
            self.divider_dotted.setStyleSheet("font-weight: normal;")
            
            if style == 'solid':
                self.divider_solid.setStyleSheet("font-weight: bold;")
            elif style == 'dashed':
                self.divider_dashed.setStyleSheet("font-weight: bold;")
            elif style == 'dotted':
                self.divider_dotted.setStyleSheet("font-weight: bold;")
                
            # Atualizar cor do divisor
            color = QColor(props.get('borderColor', '#ccc'))
            self.divider_color_btn.setStyleSheet(f"background-color: {color.name()};")
            
            # Atualiza o valor da espessura do divisor
            border_width = props.get('borderWidth', '1px')
            if border_width:
                try:
                    # Extrai o valor numérico da string (ex: '2px' -> 2)
                    width_value = int(border_width.replace('px', ''))
                    self.divider_thickness_spin.setValue(width_value)
                except (ValueError, AttributeError):
                    self.divider_thickness_spin.setValue(1)
        elif self.current_component_type in ["two-columns", "three-columns"]:
            # Atualizar espaçamento entre colunas
            gap = props.get('gap', '20px')
            if gap:
                try:
                    gap_value = int(gap.replace('px', ''))
                    self.columns_gap_spin.setValue(gap_value)
                except (ValueError, AttributeError):
                    self.columns_gap_spin.setValue(20)
        elif self.current_component_type == "social":
            # Atualizar tamanho dos ícones
            icon_size = props.get('iconSize', '32px')
            if icon_size:
                try:
                    size_value = int(icon_size.replace('px', ''))
                    self.social_size_spin.setValue(size_value)
                except (ValueError, AttributeError):
                    self.social_size_spin.setValue(32)
                    
            # Destacar o botão de alinhamento ativo
            align = props.get('align', 'center')
            self.social_align_left.setStyleSheet("font-weight: normal;")
            self.social_align_center.setStyleSheet("font-weight: normal;")
            self.social_align_right.setStyleSheet("font-weight: normal;")
            
            if align == 'left':
                self.social_align_left.setStyleSheet("font-weight: bold;")
            elif align == 'center':
                self.social_align_center.setStyleSheet("font-weight: bold;")
            elif align == 'right':
                self.social_align_right.setStyleSheet("font-weight: bold;")
        elif self.current_component_type == "video":
            # Atualizar URL do vídeo e da thumbnail
            thumbnail = props.get('thumbnailUrl', '')
            video_url = props.get('videoUrl', '')
            self.video_url_edit.setText(video_url)
            self.video_thumbnail_edit.setText(thumbnail)
        elif self.current_component_type == "html":
            # Atualizar conteúdo HTML
            html_content = props.get('htmlContent', '')
            # Preservar o conteúdo HTML exatamente como está no componente
            
            self.html_content_edit.setPlainText(html_content)
            
        self.blockSignals(False)

    def clear_properties(self):
        self.current_component_id = None
        self.current_component_type = None
        self.stacked_widget.setCurrentIndex(0)
        
        # Oculta os controles de componente
        self.component_controls.setVisible(False)
        
        # Oculta os controles de estilo comuns
        self.style_controls.setVisible(False)
        
        # Oculta os controles de bordas arredondadas
        self.corner_controls.setVisible(False)

    def emit_change(self, prop_name, value):
        if self.current_component_id:
            self.property_changed.emit(self.current_component_id, prop_name, value)
            
    def pick_button_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.button_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.emit_change("bgColor", color.name())
            
    def pick_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color_btn.setStyleSheet(f"color: {color.name()};")
            self.emit_change("color", color.name())
            
    def pick_button_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.button_text_color_btn.setStyleSheet(f"color: {color.name()};")
            self.emit_change("textColor", color.name())
            
    def pick_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            # Não altera a cor do botão, apenas emite o sinal para mudar a cor de fundo do email
            self.property_changed.emit("", "bgColor", color.name())
            
    def pick_component_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            # Não altera a cor do botão, apenas emite o sinal para mudar a cor de fundo do componente
            # Emite a mudança para atualizar a cor de fundo do componente
            self.emit_change("backgroundColor", color.name())
            
    def set_border_radius(self, value):
        self.emit_change("borderRadius", value)
        
    def show_border_radius_controls(self):
        # Mostra os controles de raio de borda individuais
        self.corner_controls.setVisible(True)
        
    def update_all_corners(self, value):
        # Atualiza todos os spinners com o mesmo valor
        self.blockSignals(True)
        self.top_left_spin.setValue(value)
        self.top_right_spin.setValue(value)
        self.bottom_left_spin.setValue(value)
        self.bottom_right_spin.setValue(value)
        self.blockSignals(False)
        
        # Emite a mudança para todos os cantos
        radius_value = f"{value}px"
        self.emit_change("borderRadius", radius_value)
            
    def request_delete(self):
        self.delete_component.emit()
        
    def request_move_up(self):
        self.move_component_up.emit()
        
    def request_move_down(self):
        self.move_component_down.emit()
        
    def request_image_upload(self):
        if self.current_component_id:
            self.upload_image.emit(self.current_component_id)
            
    def load_custom_font(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Fonte", "", "Arquivos de Fonte (*.ttf *.otf)"
        )
        
        if file_path:
            # Extrair o nome da fonte do caminho do arquivo
            import os
            font_name = os.path.basename(file_path).split('.')[0]
            font_path = file_path.replace('\\', '/')
            
            # Criar uma regra CSS para a fonte personalizada
            custom_font = f"'{font_name}', sans-serif"
            self.emit_change("fontFamily", custom_font)
            
            # Informar ao usuário
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Fonte Carregada", f"A fonte {font_name} foi aplicada ao componente.")
    
    def load_custom_font_button(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Fonte", "", "Arquivos de Fonte (*.ttf *.otf)"
        )
        
        if file_path:
            # Extrair o nome da fonte do caminho do arquivo
            import os
            font_name = os.path.basename(file_path).split('.')[0]
            font_path = file_path.replace('\\', '/')
            
            # Criar uma regra CSS para a fonte personalizada
            custom_font = f"'{font_name}', sans-serif"
            self.emit_change("fontFamily", custom_font)
            
            # Informar ao usuário
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Fonte Carregada", f"A fonte {font_name} foi aplicada ao botão.")
            
    def pick_divider_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.divider_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.emit_change("borderColor", color.name())
            
    def request_video_thumbnail_upload(self):
        if self.current_component_id:
            self.upload_image.emit(self.current_component_id)

    def insert_html_tag(self, opening_tag, closing_tag):
        # Insere tags HTML no cursor ou ao redor do texto selecionado
        cursor = self.html_content_edit.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text:
            # Se há texto selecionado, envolve-o com as tags
            new_text = opening_tag + selected_text + closing_tag
            cursor.insertText(new_text)
        else:
            # Se não há texto selecionado, apenas insere as tags e posiciona o cursor entre elas
            cursor.insertText(opening_tag + closing_tag)
            # Move o cursor para entre as tags
            from PySide6.QtGui import QTextCursor
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(closing_tag))
            self.html_content_edit.setTextCursor(cursor)
            
    def adjust_text_edit_height(self):
        # Ajusta a altura do QTextEdit conforme o conteúdo
        document = self.text_content_edit.document()
        margins = self.text_content_edit.contentsMargins()
        doc_height = document.size().height() + margins.top() + margins.bottom() + 10  # Adiciona um pouco de espaço extra
        
        # Define uma altura mínima e máxima para o QTextEdit
        min_height = 80
        max_height = 300
        
        # Ajusta a altura dentro dos limites
        new_height = max(min_height, min(doc_height, max_height))
        self.text_content_edit.setMinimumHeight(new_height)
        from PySide6.QtCore import QSize
        
        # Obter o tamanho do documento
        document = self.text_content_edit.document()
        document_size = document.size().toSize()
        
        # Calcular a altura necessária (altura do documento + margens)
        margins = self.text_content_edit.contentsMargins()
        height = document_size.height() + margins.top() + margins.bottom() + 10  # 10px extra para evitar barra de rolagem
        
        # Definir altura mínima e máxima
        min_height = 80
        max_height = 300
        
        # Ajustar a altura dentro dos limites
        new_height = max(min_height, min(height, max_height))
        
        # Aplicar a nova altura
        self.text_content_edit.setMinimumHeight(new_height)