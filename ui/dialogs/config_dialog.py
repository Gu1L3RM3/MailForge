from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt
from core.config_manager import ConfigManager

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações de Email")
        self.setMinimumWidth(400)
        
        # Inicializar o gerenciador de configurações
        self.config_manager = ConfigManager()
        
        # Carregar configurações existentes
        self.current_config = self.config_manager.load_email_config()
        
        # Configurar a interface
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Grupo de configurações de email
        email_group = QGroupBox("Configurações de Conta")
        email_layout = QFormLayout(email_group)
        
        # Campo de email
        self.email_edit = QLineEdit(self.current_config.get('email', ''))
        email_layout.addRow("Email:", self.email_edit)
        
        # Campo de senha
        self.password_edit = QLineEdit(self.current_config.get('password', ''))
        self.password_edit.setEchoMode(QLineEdit.Password)
        email_layout.addRow("Senha:", self.password_edit)
        
        # Informações sobre o servidor SMTP
        info_label = QLabel(
            "<p>Estas configurações serão usadas para enviar emails através do seu provedor.</p>"
            "<p>Para o Gmail, você pode precisar criar uma <a href='https://myaccount.google.com/apppasswords'>senha de aplicativo</a>.</p>"
        )
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        
        # Botões
        buttons_layout = QVBoxLayout()
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.clicked.connect(self.save_config)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        # Adicionar widgets ao layout principal
        layout.addWidget(email_group)
        layout.addWidget(info_label)
        layout.addLayout(buttons_layout)
    
    def save_config(self):
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        # Validação básica
        if not email:
            QMessageBox.warning(self, "Campos Incompletos", "Por favor, informe seu endereço de email.")
            return
        
        # Salvar configurações
        try:
            self.config_manager.save_email_config(email, password)
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar as configurações: {e}")