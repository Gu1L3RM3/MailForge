import os
import sys
import json
import base64
from cryptography.fernet import Fernet
from core.resource_path import get_resource_path

class ConfigManager:
    def __init__(self):
        # Determinar o diretório base para armazenar configurações
        try:
            # Se estiver em um executável PyInstaller
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            # Fallback para o diretório do usuário se não conseguir determinar
            base_dir = os.path.expanduser('~')
            
        self.app_data_dir = os.path.join(base_dir, 'config')
        self.config_dir = self.app_data_dir
        self.config_file = os.path.join(self.config_dir, 'email_config.json')
        self.key_file = os.path.join(self.config_dir, 'key.bin')
        
        # Garantir que o diretório de configuração existe
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
        except Exception as e:
            print(f"Erro ao criar diretório de configuração: {e}")
            # Fallback para o diretório temporário
            import tempfile
            self.app_data_dir = os.path.join(tempfile.gettempdir(), 'mailforge')
            self.config_dir = self.app_data_dir
            self.config_file = os.path.join(self.config_dir, 'email_config.json')
            self.key_file = os.path.join(self.config_dir, 'key.bin')
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
        
        # Inicializar ou carregar a chave de criptografia
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Inicializa ou carrega a chave de criptografia"""
        if not os.path.exists(self.key_file):
            # Gerar uma nova chave
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        else:
            # Carregar chave existente
            with open(self.key_file, 'rb') as f:
                key = f.read()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Criptografa uma string"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        """Descriptografa uma string"""
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return ""
    
    def save_email_config(self, email, password):
        """Salva as configurações de email criptografadas"""
        config = {
            'email': email,
            'password': self.encrypt(password) if password else ""
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        
        # Atualizar o arquivo .env para compatibilidade com código existente
        self._update_env_file(email, password)
        
        return True
    
    def load_email_config(self):
        """Carrega as configurações de email"""
        if not os.path.exists(self.config_file):
            return {
                'email': "",
                'password': ""
            }
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Descriptografar a senha
            if config.get('password'):
                config['password'] = self.decrypt(config['password'])
            
            return config
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return {
                'email': "",
                'password': ""
            }
    
    def _update_env_file(self, email, password):
        """Atualiza o arquivo .env com as novas configurações"""
        env_path = os.path.join(self.app_data_dir, '.env')
        
        # Criar conteúdo do arquivo .env
        env_content = f'''EMAIL_REMETENTE="{email}"
EMAIL_PASSWORD="{password}"'''
        
        with open(env_path, 'w') as f:
            f.write(env_content)