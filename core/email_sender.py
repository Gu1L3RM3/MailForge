import smtplib
import os
import base64
import re
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from urllib.parse import urlparse, unquote

def process_images_in_html(html_body):
    """
    Processa imagens no HTML, convertendo URLs locais em imagens embutidas com CID.
    Retorna o HTML modificado e um dicionário de imagens para anexar.
    """
    images_to_attach = {}
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\'>]+)["\'][^>]*>', re.IGNORECASE)
    
    def replace_image_src(match):
        src = match.group(1)
        parsed_url = urlparse(src)
        
        # Verifica se é uma URL local (file://) ou um caminho de arquivo
        if parsed_url.scheme == 'file' or not parsed_url.scheme:
            # Extrai o caminho do arquivo
            if parsed_url.scheme == 'file':
                file_path = unquote(parsed_url.path.lstrip('/'))
                # No Windows, ajusta o caminho
                if os.name == 'nt' and file_path.startswith('/'):
                    file_path = file_path[1:]
            else:
                file_path = src
                
            # Verifica se o arquivo existe
            if os.path.isfile(file_path):
                try:
                    # Gera um ID único para a imagem
                    img_id = f"img_{len(images_to_attach) + 1}"
                    cid = f"<{img_id}>"
                    
                    # Lê o arquivo de imagem
                    with open(file_path, 'rb') as img_file:
                        img_data = img_file.read()
                    
                    # Determina o tipo MIME com base na extensão
                    ext = os.path.splitext(file_path)[1].lower()
                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.bmp': 'image/bmp'
                    }.get(ext, 'application/octet-stream')
                    
                    # Armazena a imagem para anexar depois
                    images_to_attach[img_id] = (img_data, mime_type)
                    
                    # Substitui o src pela referência CID
                    return match.group(0).replace(src, f"cid:{img_id}")
                except Exception as e:
                    print(f"Erro ao processar imagem {file_path}: {e}")
                    return match.group(0)
            else:
                # Se o arquivo não existe, mantém a URL original
                return match.group(0)
        else:
            # Se não for uma URL local, mantém a URL original
            return match.group(0)
    
    # Substitui todas as ocorrências de imagens no HTML
    modified_html = img_pattern.sub(replace_image_src, html_body)
    
    return modified_html, images_to_attach

def send_email(smtp_config, recipients, subject, html_body, attachments=None):
    """
    Envia email para uma lista de destinatários.
    Parâmetros:
        smtp_config: Dicionário com configurações SMTP (host, port, user, password)
        recipients: Lista de emails destinatários
        subject: Assunto do email
        html_body: Conteúdo HTML do email
        attachments: Lista de caminhos para arquivos a serem anexados
    Retorna (sucesso, mensagem)
    """
    try:
        # Tenta com SSL primeiro, que é mais comum
        try:
            server = smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port'])
        except Exception:
            # Se falhar, tenta com TLS
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            server.starttls()
            
        server.login(smtp_config['user'], smtp_config['password'])

        sent_count = 0
        for recipient in recipients:
            if not recipient.strip():
                continue
            
            # Processa imagens no HTML
            modified_html, images_to_attach = process_images_in_html(html_body)
            
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = smtp_config['user']
            msg['To'] = recipient.strip()

            # Adiciona a parte HTML
            html_part = MIMEText(modified_html, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Adiciona as imagens como anexos inline
            for img_id, (img_data, mime_type) in images_to_attach.items():
                img = MIMEImage(img_data, _subtype=mime_type.split('/')[1])
                img.add_header('Content-ID', img_id)
                img.add_header('Content-Disposition', 'inline')
                msg.attach(img)
            
            # Adiciona os anexos
            if attachments:
                for attachment_path in attachments:
                    if os.path.isfile(attachment_path):
                        try:
                            # Determina o tipo MIME com base na extensão
                            content_type, encoding = mimetypes.guess_type(attachment_path)
                            if content_type is None or encoding is not None:
                                content_type = 'application/octet-stream'
                            maintype, subtype = content_type.split('/', 1)
                            
                            # Lê o arquivo
                            with open(attachment_path, 'rb') as f:
                                attachment_data = f.read()
                            
                            # Cria o anexo
                            if maintype == 'text':
                                attachment = MIMEText(attachment_data.decode('utf-8'), _subtype=subtype)
                            elif maintype == 'image':
                                attachment = MIMEImage(attachment_data, _subtype=subtype)
                            else:
                                attachment = MIMEApplication(attachment_data, _subtype=subtype)
                            
                            # Adiciona o cabeçalho com o nome do arquivo
                            filename = os.path.basename(attachment_path)
                            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                            msg.attach(attachment)
                        except Exception as e:
                            print(f"Erro ao anexar arquivo {attachment_path}: {e}")
            
            server.send_message(msg)
            sent_count += 1
        
        server.quit()
        return True, f"{sent_count} de {len(recipients)} emails enviados com sucesso!"
    except smtplib.SMTPAuthenticationError:
        return False, "Falha na autenticação. Verifique seu usuário e senha."
    except Exception as e:
        return False, f"Falha no envio: {e}"