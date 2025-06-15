import os
import sys
import cairosvg
from PIL import Image

def svg_to_ico(svg_path, ico_path, sizes=[16, 32, 48, 64, 128, 256]):
    """Converte um arquivo SVG para ICO com múltiplos tamanhos"""
    # Cria um diretório temporário para os PNGs intermediários
    temp_dir = os.path.join(os.path.dirname(svg_path), 'temp_icons')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Lista para armazenar as imagens de diferentes tamanhos
    images = []
    
    try:
        # Converte SVG para PNGs de diferentes tamanhos
        for size in sizes:
            png_path = os.path.join(temp_dir, f'icon_{size}.png')
            cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=size, output_height=size)
            img = Image.open(png_path)
            images.append(img)
        
        # Salva as imagens como um arquivo ICO
        images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
        print(f"Ícone ICO criado com sucesso: {ico_path}")
        
    except Exception as e:
        print(f"Erro ao converter SVG para ICO: {e}")
    finally:
        # Limpa os arquivos temporários
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

if __name__ == "__main__":
    svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.svg')
    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.ico')
    svg_to_ico(svg_path, ico_path)