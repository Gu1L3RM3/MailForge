import os
import sys

def get_resource_path(relative_path):
    """
    Retorna o caminho absoluto para um recurso, funcionando tanto em modo de desenvolvimento
    quanto em modo de execução via PyInstaller.
    
    Args:
        relative_path (str): Caminho relativo ao diretório base do aplicativo
        
    Returns:
        str: Caminho absoluto para o recurso
    """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver em um executável, usa o diretório do script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    return os.path.join(base_path, relative_path)