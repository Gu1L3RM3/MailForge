import os
import sys
import subprocess
import platform

def build_executable():
    """Cria um executável do aplicativo usando PyInstaller"""
    # Verifica se o PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Caminho para o ícone (usando .ico em vez de .svg)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.ico')
    
    # Verifica se o ícone existe, se não, cria um ícone simples
    if not os.path.exists(icon_path):
        svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.svg')
        if os.path.exists(svg_path):
            print(f"Tentando converter SVG para ICO...")
            try:
                # Tenta primeiro usar a conversão SVG se disponível
                try:
                    from convert_icon import svg_to_ico
                    svg_to_ico(svg_path, icon_path)
                except ImportError as e:
                    print(f"Módulo cairosvg não disponível: {e}")
                    raise Exception("Conversão SVG falhou")
            except Exception as e:
                print(f"Erro ao converter SVG para ICO: {e}")
                print("Criando um ícone simples como alternativa...")
                try:
                    # Usa a função alternativa para criar um ícone simples
                    from create_icon import create_simple_ico
                    if not create_simple_ico(icon_path):
                        print("Erro ao criar ícone simples.")
                        return
                except Exception as e:
                    print(f"Erro ao criar ícone simples: {e}")
                    return
        else:
            print(f"Aviso: Nenhum arquivo SVG encontrado. Criando um ícone simples...")
            try:
                from create_icon import create_simple_ico
                if not create_simple_ico(icon_path):
                    print("Erro ao criar ícone simples.")
                    return
            except Exception as e:
                print(f"Erro ao criar ícone simples: {e}")
                return
    
    # Comando para o PyInstaller
    cmd = [
        "pyinstaller",
        "--name=MailForge",
        "--windowed",  # Sem console
        "--onefile",  # Gera um único arquivo executável
        f"--icon={icon_path}",
        "--add-data=assets;assets",  # Inclui a pasta assets
        "--add-data=styles;styles",  # Inclui a pasta styles
        "--add-data=core;core",  # Inclui a pasta core
        "--add-data=ui;ui",  # Inclui a pasta ui
        "--noconfirm",  # Não pede confirmação para sobrescrever
        "--clean",  # Limpa cache antes de construir
        "main.py"  # Arquivo principal
    ]
    
    print("Iniciando a criação do executável...")
    subprocess.check_call(cmd)
    print("Executável criado com sucesso!")
    print(f"O executável está localizado em: {os.path.abspath('dist/MailForge.exe')}")

if __name__ == "__main__":
    build_executable()