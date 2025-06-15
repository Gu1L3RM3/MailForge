from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QTabWidget, QWidget, QPlainTextEdit,
                             QListWidget, QFileDialog, QMessageBox, QLabel, QSpinBox,
                             QHBoxLayout, QGroupBox)
from core.excel_reader import get_emails_from_excel
from core.email_sender import send_email
from core.config_manager import ConfigManager
import os

class SendDialog(QDialog):
    def __init__(self, html_content, parent=None):
        super().__init__(parent)
        self.html_content = html_content
        self.setWindowTitle("Enviar Email")
        self.setMinimumWidth(500)

        # Obter configurações do gerenciador de configurações
        config_manager = ConfigManager()
        email_config = config_manager.load_email_config()
        
        self.email_remetente = email_config.get('email', '')
        self.email_password = email_config.get('password', '')
        self.smtp_host = "smtp.gmail.com"  # Valor padrão para Gmail
        self.smtp_port = 587  # Valor padrão para Gmail

        self.layout = QVBoxLayout(self)

        # SMTP Config
        self.smtp_group = QWidget()
        self.smtp_layout = QFormLayout(self.smtp_group)
        self.subject_edit = QLineEdit("Assunto do seu email")
        
        # Mostrar o email do remetente como informação, não como campo editável
        self.email_info = QLabel(f"<b>Email remetente:</b> {self.email_remetente}")
        
        # Adicionar um botão para configurar o email se não estiver configurado
        if not self.email_remetente or not self.email_password:
            self.config_warning = QLabel("<font color='red'>⚠️ Credenciais de email não configuradas!</font>")
            self.config_button = QPushButton("Configurar Email")
            self.config_button.clicked.connect(self.open_config_dialog)
            self.smtp_layout.addRow(self.config_warning)
            self.smtp_layout.addRow(self.config_button)
        
        self.smtp_layout.addRow("Assunto:", self.subject_edit)
        self.smtp_layout.addRow(self.email_info)

        # Recipients
        self.tabs = QTabWidget()
        self.setup_manual_tab()
        self.setup_excel_tab()
        
        # Seção de Anexos
        self.setup_attachments_section()
        
        # Send Button
        self.send_button = QPushButton("Enviar Emails")
        self.send_button.clicked.connect(self.handle_send)

        self.layout.addWidget(QLabel("<b>Configurações de Envio (SMTP)</b>"))
        self.layout.addWidget(self.smtp_group)
        self.layout.addWidget(QLabel("<b>Destinatários</b>"))
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(QLabel("<b>Anexos</b>"))
        self.layout.addWidget(self.attachments_group)
        self.layout.addWidget(self.send_button)

    def setup_manual_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Digite ou cole os emails, um por linha:"))
        self.manual_emails_edit = QPlainTextEdit()
        layout.addWidget(self.manual_emails_edit)
        self.tabs.addTab(widget, "Digitar Manualmente")

    def setup_excel_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.load_excel_button = QPushButton("Carregar Planilha Excel")
        self.load_excel_button.clicked.connect(self.load_from_excel)
        self.excel_email_list = QListWidget()
        self.excel_status_label = QLabel("Nenhum arquivo carregado.")
        
        layout.addWidget(self.load_excel_button)
        layout.addWidget(self.excel_status_label)
        layout.addWidget(self.excel_email_list)
        self.tabs.addTab(widget, "Importar de Excel")

    def load_from_excel(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir Planilha", "", "Arquivos Excel (*.xlsx *.xls)")
        if filepath:
            emails, message = get_emails_from_excel(filepath)
            self.excel_status_label.setText(message)
            if emails:
                self.excel_email_list.clear()
                self.excel_email_list.addItems(emails)
            else:
                QMessageBox.warning(self, "Erro ao Ler Planilha", message)
    
    def get_recipients(self):
        if self.tabs.currentIndex() == 0: # Manual
            return self.manual_emails_edit.toPlainText().splitlines()
        else: # Excel
            return [self.excel_email_list.item(i).text() for i in range(self.excel_email_list.count())]

    def setup_attachments_section(self):
        self.attachments_group = QGroupBox()
        layout = QVBoxLayout(self.attachments_group)
        
        # Lista de anexos
        self.attachments_list = QListWidget()
        self.attachments_list.setMinimumHeight(100)
        
        # Botões para adicionar/remover anexos
        buttons_layout = QHBoxLayout()
        self.add_attachment_button = QPushButton("Adicionar Anexo")
        self.add_attachment_button.clicked.connect(self.add_attachment)
        self.remove_attachment_button = QPushButton("Remover Anexo")
        self.remove_attachment_button.clicked.connect(self.remove_attachment)
        
        buttons_layout.addWidget(self.add_attachment_button)
        buttons_layout.addWidget(self.remove_attachment_button)
        
        layout.addWidget(self.attachments_list)
        layout.addLayout(buttons_layout)
    
    def add_attachment(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar Anexos", "", "Todos os Arquivos (*.*)"
        )
        
        for file_path in file_paths:
            # Verifica se o arquivo já está na lista
            items = self.attachments_list.findItems(file_path, Qt.MatchExactly)
            if not items:
                self.attachments_list.addItem(file_path)
    
    def remove_attachment(self):
        selected_items = self.attachments_list.selectedItems()
        for item in selected_items:
            self.attachments_list.takeItem(self.attachments_list.row(item))
    
    def get_attachments(self):
        attachments = []
        for i in range(self.attachments_list.count()):
            attachments.append(self.attachments_list.item(i).text())
        return attachments
    
    def handle_send(self):
        smtp_config = {
            "host": self.smtp_host,
            "port": self.smtp_port,
            "user": self.email_remetente,
            "password": self.email_password
        }
        
        recipients = self.get_recipients()
        subject = self.subject_edit.text()
        attachments = self.get_attachments()

        if not all(smtp_config.values()) or not recipients or not subject:
            if not smtp_config['user'] or not smtp_config['password']:
                QMessageBox.warning(self, "Credenciais Não Configuradas", "Por favor, configure suas credenciais de email antes de enviar.")
                self.open_config_dialog()
                return
            else:
                QMessageBox.warning(self, "Campos Incompletos", "Por favor, preencha o assunto e adicione pelo menos um destinatário.")
                return

        self.send_button.setEnabled(False)
        self.send_button.setText("Enviando...")

        success, message = send_email(smtp_config, recipients, subject, self.html_content, attachments)

        if success:
            QMessageBox.information(self, "Envio Concluído", message)
            self.accept() # Fecha o diálogo
        else:
            QMessageBox.critical(self, "Erro no Envio", message)
            self.send_button.setEnabled(True)
            self.send_button.setText("Enviar Emails")
        
    def open_config_dialog(self):
        """Abre o diálogo de configurações de email"""
        from ui.dialogs.config_dialog import ConfigDialog
        dialog = ConfigDialog(self)
        if dialog.exec():
            # Recarregar as configurações após salvar
            config_manager = ConfigManager()
            email_config = config_manager.load_email_config()
            
            self.email_remetente = email_config.get('email', '')
            self.email_password = email_config.get('password', '')
            
            # Atualizar a interface
            self.email_info.setText(f"<b>Email remetente:</b> {self.email_remetente}")
            
            # Remover avisos se as credenciais foram configuradas
            if hasattr(self, 'config_warning') and self.email_remetente and self.email_password:
                self.config_warning.setVisible(False)
                self.config_button.setVisible(False)