import os
import sys
from PIL import Image, ImageDraw

def create_simple_ico(ico_path, size=256, bg_color="#3498db", fg_color="#ffffff"):
    """Cria um ícone ICO simples programaticamente"""
    # Cria imagens em diferentes tamanhos
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for img_size in sizes:
        # Cria uma nova imagem com fundo azul
        img = Image.new('RGBA', (img_size, img_size), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Desenha um envelope simples
        margin = int(img_size * 0.2)
        width = img_size - 2 * margin
        height = int(width * 0.6)  # Proporção do envelope
        
        # Corpo do envelope
        draw.rectangle(
            [margin, margin + int(img_size * 0.1), 
             img_size - margin, margin + int(img_size * 0.1) + height],
            fill=fg_color, outline=bg_color
        )
        
        # Parte superior do envelope (triângulo)
        draw.polygon(
            [
                (margin, margin + int(img_size * 0.1)),
                (img_size // 2, margin + int(img_size * 0.25)),
                (img_size - margin, margin + int(img_size * 0.1))
            ],
            fill=bg_color
        )
        
        # Linhas representando conteúdo
        line_margin = int(img_size * 0.05)
        line_height = int(img_size * 0.03)
        line_y = margin + int(img_size * 0.25)
        
        for i in range(3):
            draw.rectangle(
                [margin + line_margin, line_y + i * (line_height * 2),
                 img_size - margin - line_margin, line_y + i * (line_height * 2) + line_height],
                fill="#e0e0e0"
            )
        
        # Adiciona a imagem à lista
        images.append(img)
    
    # Salva as imagens como um arquivo ICO
    try:
        # Cria o diretório pai se não existir
        os.makedirs(os.path.dirname(ico_path), exist_ok=True)
        
        # Salva o arquivo ICO com múltiplos tamanhos
        images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
        print(f"Ícone ICO criado com sucesso: {ico_path}")
        return True
    except Exception as e:
        print(f"Erro ao criar ICO: {e}")
        return False

if __name__ == "__main__":
    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'app_icon.ico')
    create_simple_ico(ico_path)