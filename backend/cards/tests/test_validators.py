"""
MTG Translator — Testes de Validadores de Upload

Cobre todos os cenários de validação de segurança:
- Arquivo válido (JPEG/PNG)
- Arquivo vazio ou None
- Tamanho excedido
- Extensão inválida
- Extensão dupla maliciosa
- Magic bytes inválidos (arquivo mascarado)
- Path traversal
- Sanitização de nomes
"""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError

from cards.validators import validate_image_file, sanitize_filename


import io
from PIL import Image

class TestValidateImageFile(TestCase):
    """Testes para a função validate_image_file."""

    def _make_jpeg(self, size: int = 1024, name: str = 'test.jpg') -> SimpleUploadedFile:
        """Cria um arquivo JPEG válido para testes."""
        file_obj = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file_obj, format='JPEG')
        file_obj.seek(0)
        
        content = file_obj.read()
        if len(content) < size:
            content += b'\x00' * (size - len(content))
            
        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type='image/jpeg',
        )

    def _make_png(self, size: int = 1024, name: str = 'test.png') -> SimpleUploadedFile:
        """Cria um arquivo PNG válido para testes."""
        file_obj = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(file_obj, format='PNG')
        file_obj.seek(0)
        
        content = file_obj.read()
        if len(content) < size:
            content += b'\x00' * (size - len(content))

        return SimpleUploadedFile(
            name=name,
            content=content,
            content_type='image/png',
        )

    # ── Cenários de Sucesso ──

    def test_valid_jpeg_passes(self):
        """JPEG válido deve passar na validação."""
        f = self._make_jpeg()
        # Não deve levantar exceção
        validate_image_file(f)

    def test_valid_png_passes(self):
        """PNG válido deve passar na validação."""
        f = self._make_png()
        validate_image_file(f)

    # ── Arquivo None ou Vazio ──

    def test_none_file_raises(self):
        """Arquivo None deve ser rejeitado."""
        with self.assertRaises(ValidationError) as ctx:
            validate_image_file(None)
        self.assertIn('image', ctx.exception.detail)

    def test_empty_file_raises(self):
        """Arquivo vazio (0 bytes) deve ser rejeitado."""
        f = SimpleUploadedFile('empty.jpg', b'', content_type='image/jpeg')
        with self.assertRaises(ValidationError) as ctx:
            validate_image_file(f)
        self.assertIn('image', ctx.exception.detail)

    # ── Tamanho Excedido ──

    @override_settings(MAX_UPLOAD_SIZE_MB=1)
    def test_oversized_file_raises(self):
        """Arquivo maior que o limite (1MB para teste) deve ser rejeitado."""
        # 1.5MB
        f = self._make_jpeg(size=1_500_000)
        with self.assertRaises(ValidationError) as ctx:
            validate_image_file(f)
        error_msg = str(ctx.exception.detail['image'])
        self.assertIn('excede', error_msg.lower())

    @override_settings(MAX_UPLOAD_SIZE_MB=5)
    def test_file_within_limit_passes(self):
        """Arquivo dentro do limite deve passar."""
        # 4MB (abaixo de 5MB)
        f = self._make_jpeg(size=4_000_000)
        validate_image_file(f)

    # ── Extensão Inválida ──

    def test_invalid_extension_raises(self):
        """Arquivo com extensão não permitida deve ser rejeitado."""
        content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        f = SimpleUploadedFile('test.gif', content, content_type='image/gif')
        with self.assertRaises(ValidationError) as ctx:
            validate_image_file(f)
        error_msg = str(ctx.exception.detail['image'])
        self.assertIn('.gif', error_msg)

    def test_exe_extension_raises(self):
        """Arquivo .exe deve ser rejeitado."""
        content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        f = SimpleUploadedFile('hack.exe', content, content_type='image/jpeg')
        with self.assertRaises(ValidationError):
            validate_image_file(f)

    # ── Extensão Dupla Maliciosa ──

    def test_double_extension_exe_raises(self):
        """Extensão dupla com .exe deve ser bloqueada."""
        content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        f = SimpleUploadedFile(
            'carta.exe.jpg', content, content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError):
            validate_image_file(f)

    def test_double_extension_php_raises(self):
        """Extensão dupla com .php deve ser bloqueada."""
        content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        f = SimpleUploadedFile(
            'shell.php.png', content, content_type='image/png'
        )
        with self.assertRaises(ValidationError):
            validate_image_file(f)

    def test_harmless_dots_in_name_passes(self):
        """Nomes com pontos inofensivos (ex: my.card.foto.jpg) devem passar."""
        content = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        f = SimpleUploadedFile(
            'my.card.foto.jpg', content, content_type='image/jpeg'
        )
        # Não deve levantar exceção
        validate_image_file(f)

    # ── Magic Bytes Inválidos ──

    def test_text_file_masquerading_as_jpeg_raises(self):
        """Arquivo texto renomeado para .jpg deve ser rejeitado."""
        content = b'This is not an image, just plain text content.'
        f = SimpleUploadedFile('fake.jpg', content, content_type='image/jpeg')
        with self.assertRaises(ValidationError) as ctx:
            validate_image_file(f)
        error_msg = str(ctx.exception.detail['image'])
        self.assertIn('imagem', error_msg.lower())

    def test_pdf_masquerading_as_png_raises(self):
        """Arquivo PDF renomeado para .png deve ser rejeitado."""
        content = b'%PDF-1.4 fake pdf content here'
        f = SimpleUploadedFile('carta.png', content, content_type='image/png')
        with self.assertRaises(ValidationError):
            validate_image_file(f)

    # ── Path Traversal ──

    def test_path_traversal_dotdot_raises(self):
        """Nome com '..' deve ser rejeitado (Path Traversal)."""
        f = self._make_jpeg()
        f.name = '../../../etc/passwd.jpg'  # Forçar nome ignorando normalização
        with self.assertRaises(ValidationError):
            validate_image_file(f)

    def test_path_traversal_backslash_raises(self):
        """Nome com '\\' deve ser rejeitado."""
        f = self._make_jpeg()
        f.name = 'folder\\hack.jpg'
        with self.assertRaises(ValidationError):
            validate_image_file(f)

    def test_null_byte_in_name_raises(self):
        """Nome com null byte deve ser rejeitado."""
        f = self._make_jpeg()
        f.name = 'image\x00.jpg'
        with self.assertRaises(ValidationError):
            validate_image_file(f)


class TestSanitizeFilename(TestCase):
    """Testes para a função sanitize_filename."""

    def test_normal_filename_unchanged(self):
        """Nome normal deve permanecer essencialmente igual."""
        result = sanitize_filename('minha_carta.jpg')
        self.assertEqual(result, 'minha_carta.jpg')

    def test_spaces_replaced(self):
        """Espaços devem ser substituídos por underscores."""
        result = sanitize_filename('minha carta foto.png')
        self.assertEqual(result, 'minha_carta_foto.png')

    def test_special_chars_removed(self):
        """Caracteres especiais devem ser removidos."""
        result = sanitize_filename('carta@#$%!.jpg')
        self.assertNotIn('@', result)
        self.assertNotIn('#', result)
        self.assertTrue(result.endswith('.jpg'))

    def test_extension_lowercased(self):
        """Extensão deve ser convertida para minúsculas."""
        result = sanitize_filename('CARTA.JPG')
        self.assertTrue(result.endswith('.jpg'))

    def test_empty_name_gets_default(self):
        """Nome vazio deve receber nome padrão."""
        result = sanitize_filename('.jpg')
        self.assertEqual(result, 'upload.jpg')

    def test_long_name_truncated(self):
        """Nome muito longo deve ser truncado."""
        long_name = 'a' * 200 + '.png'
        result = sanitize_filename(long_name)
        name_part = result.replace('.png', '')
        self.assertLessEqual(len(name_part), 100)
