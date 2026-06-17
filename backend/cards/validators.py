"""
MTG Translator — Validadores de Upload

Segurança por Design:
- Valida MIME type real via magic bytes (não apenas extensão)
- Limita tamanho máximo do arquivo
- Sanitiza nome do arquivo contra Path Traversal
- Rejeita extensões duplas
"""
import os
import re
import logging

from django.conf import settings
from rest_framework.exceptions import ValidationError

logger = logging.getLogger('cards')

# MIME types permitidos (JPEG e PNG)
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png'}
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

# Magic bytes para validação real do tipo de arquivo
MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
}


def validate_image_file(uploaded_file) -> None:
    """
    Valida um arquivo de imagem enviado pelo usuário.

    Verificações realizadas:
    1. Arquivo não é None/vazio
    2. Tamanho dentro do limite (MAX_UPLOAD_SIZE_MB)
    3. Extensão permitida (JPEG/PNG)
    4. Nome sem extensão dupla (ex: image.jpg.exe)
    5. MIME type real via magic bytes
    6. Nome sanitizado contra path traversal

    Args:
        uploaded_file: Arquivo enviado via multipart/form-data

    Raises:
        ValidationError: Se qualquer validação falhar
    """
    # 1. Arquivo existe?
    if uploaded_file is None:
        raise ValidationError({
            'image': 'Nenhuma imagem foi enviada. Envie um arquivo JPEG ou PNG.'
        })

    if uploaded_file.size == 0:
        raise ValidationError({
            'image': 'O arquivo enviado está vazio.'
        })

    # 2. Tamanho dentro do limite
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 5) * 1024 * 1024
    if uploaded_file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValidationError({
            'image': f'O arquivo excede o limite de {max_mb:.0f}MB. '
                     f'Tamanho enviado: {uploaded_file.size / (1024 * 1024):.1f}MB.'
        })

    # 3. Extensão permitida
    filename = uploaded_file.name or ''
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError({
            'image': f'Extensão "{ext}" não permitida. '
                     f'Envie apenas arquivos JPEG (.jpg, .jpeg) ou PNG (.png).'
        })

    # 4. Extensão dupla (ex: foto.jpg.exe, carta.png.bat)
    name_without_ext = os.path.splitext(filename)[0]
    if '.' in name_without_ext:
        second_ext = os.path.splitext(name_without_ext)[1].lower()
        # Permitir nomes como "my.card.jpg" mas bloquear "card.exe.jpg"
        dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.ps1',
            '.vbs', '.js', '.wsf', '.sh', '.php', '.py', '.rb',
        }
        if second_ext in dangerous_extensions:
            logger.warning(
                'Upload bloqueado — extensão dupla suspeita: %s', filename
            )
            raise ValidationError({
                'image': 'Nome de arquivo inválido. Extensões duplas não são permitidas.'
            })

    # 5. Validação de magic bytes (MIME type real)
    uploaded_file.seek(0)
    file_header = uploaded_file.read(16)
    uploaded_file.seek(0)  # Reset para uso posterior

    detected_mime = None
    for magic, mime_type in MAGIC_BYTES.items():
        if file_header.startswith(magic):
            detected_mime = mime_type
            break

    if detected_mime is None:
        logger.warning(
            'Upload bloqueado — magic bytes inválidos: %s (header: %s)',
            filename, file_header[:8].hex()
        )
        raise ValidationError({
            'image': 'O arquivo não é uma imagem válida. '
                     'Envie apenas arquivos JPEG ou PNG genuínos.'
        })

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise ValidationError({
            'image': f'Tipo de arquivo detectado ({detected_mime}) não é permitido.'
        })

    # 6. Sanitização do nome contra Path Traversal
    if any(char in filename for char in ['..', '/', '\\', '\x00']):
        logger.warning(
            'Upload bloqueado — tentativa de path traversal: %s', filename
        )
        raise ValidationError({
            'image': 'Nome de arquivo contém caracteres inválidos.'
        })


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza o nome do arquivo, removendo caracteres perigosos
    e mantendo apenas caracteres alfanuméricos, hifens e underscores.

    Args:
        filename: Nome original do arquivo

    Returns:
        Nome sanitizado seguro para uso no sistema de arquivos
    """
    # Extrair extensão
    name, ext = os.path.splitext(filename)

    # Manter apenas caracteres seguros
    safe_name = re.sub(r'[^\w\-]', '_', name)

    # Remover underscores duplicados
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')

    # Garantir que o nome não está vazio
    if not safe_name:
        safe_name = 'upload'

    # Limitar comprimento
    safe_name = safe_name[:100]

    return f'{safe_name}{ext.lower()}'
