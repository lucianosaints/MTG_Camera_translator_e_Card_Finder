"""
MTG Translator — Testes de Integração do Endpoint

Testa o endpoint POST /api/v1/cards/identify/ de ponta a ponta,
com todas as APIs externas MOCKADAS.

Cenários obrigatórios do protocolo:
1. Caso de Sucesso: imagem válida → carta identificada → JSON completo
2. Imagem Corrompida/Inválida: arquivo texto mascarado → 400
3. Carta Não Encontrada: IA lê texto aleatório → resposta limpa
4. Falha de Integração: Scryfall/OpenRouter fora do ar → graceful degradation
"""
from unittest.mock import patch, MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status


# ─────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────

MOCK_VISION_SUCCESS = 'Lightning Bolt'
MOCK_VISION_UNIDENTIFIED = None

MOCK_SCRYFALL_RESULT = {
    'name_en': 'Lightning Bolt',
    'name_pt': 'Relâmpago',
    'type': 'Instant',
    'mana_cost': '{R}',
    'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
    'oracle_text_pt': 'Relâmpago causa 3 pontos de dano em qualquer alvo.',
    'image_url': 'https://cards.scryfall.io/large/front/l/bolt.jpg',
    'scryfall_url': 'https://scryfall.com/card/lea/161/lightning-bolt',
    'set_name': 'Alpha',
    'rarity': 'common',
    'scryfall_id': '12345-abcde',
}

ENDPOINT = '/api/v1/cards/identify/'


import io
from PIL import Image

def _make_jpeg(size: int = 1024, name: str = 'test_card.jpg') -> SimpleUploadedFile:
    """Cria um JPEG válido para testes usando Pillow."""
    file_obj = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file_obj, format='JPEG')
    file_obj.seek(0)
    
    # Adicionar padding se tamanho > gerado
    content = file_obj.read()
    if len(content) < size:
        content += b'\x00' * (size - len(content))
        
    return SimpleUploadedFile(
        name=name,
        content=content,
        content_type='image/jpeg',
    )

def _make_png(size: int = 1024, name: str = 'test_card.png') -> SimpleUploadedFile:
    """Cria um PNG válido para testes usando Pillow."""
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


from django.core.cache import cache

@override_settings(
    OPENROUTER_API_KEY='sk-test-fake-key',
    OPENROUTER_MODEL='test/model',
)
class TestCardIdentifyEndpoint(TestCase):
    """Testes de integração para POST /api/v1/cards/identify/."""

    def setUp(self):
        self.client = APIClient()
        cache.clear()  # Limpar cache de throttling para evitar erros 429 nos testes

    # ─── CENÁRIO 1: Caso de Sucesso ───

    @patch('cards.views.ScryfallService')
    @patch('cards.views.VisionService')
    def test_success_jpeg_identifies_card(self, MockVision, MockScryfall):
        """
        Upload JPEG válido → IA identifica → Scryfall retorna dados
        → Resposta 200 com JSON completo.
        """
        # Mock VisionService
        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.return_value = MOCK_VISION_SUCCESS

        # Mock ScryfallService
        mock_scryfall_instance = MockScryfall.return_value
        mock_scryfall_instance.search_card.return_value = MOCK_SCRYFALL_RESULT

        image = _make_jpeg()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['identified'])
        self.assertIsNotNone(data['card'])
        self.assertEqual(data['card']['name_en'], 'Lightning Bolt')
        self.assertEqual(data['card']['name_pt'], 'Relâmpago')
        self.assertIn('image_url', data['card'])

    @patch('cards.views.ScryfallService')
    @patch('cards.views.VisionService')
    def test_success_png_identifies_card(self, MockVision, MockScryfall):
        """Upload PNG válido também deve funcionar."""
        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.return_value = MOCK_VISION_SUCCESS

        mock_scryfall_instance = MockScryfall.return_value
        mock_scryfall_instance.search_card.return_value = MOCK_SCRYFALL_RESULT

        image = _make_png()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['identified'])

    # ─── CENÁRIO 2: Imagem Corrompida/Inválida ───

    def test_text_file_as_image_returns_400(self):
        """
        Enviar arquivo texto mascarado como imagem → 400 Bad Request.
        Magic bytes não correspondem a JPEG/PNG.
        """
        fake_image = SimpleUploadedFile(
            'fake.jpg',
            b'This is plain text, not an image!',
            content_type='image/jpeg',
        )
        response = self.client.post(ENDPOINT, {'image': fake_image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_payload_returns_400(self):
        """Payload sem arquivo → 400 Bad Request."""
        response = self.client.post(ENDPOINT, {}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_file_returns_400(self):
        """Arquivo com 0 bytes → 400 Bad Request."""
        empty_file = SimpleUploadedFile(
            'empty.jpg', b'', content_type='image/jpeg'
        )
        response = self.client.post(ENDPOINT, {'image': empty_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(MAX_UPLOAD_SIZE_MB=1)
    def test_oversized_file_returns_400(self):
        """Arquivo > limite (1MB) → 400 Bad Request."""
        big_file = _make_jpeg(size=1_500_000)
        response = self.client.post(ENDPOINT, {'image': big_file}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ─── CENÁRIO 3: Carta Não Encontrada ───

    @patch('cards.views.VisionService')
    def test_ai_cannot_identify_returns_not_identified(self, MockVision):
        """
        IA retorna UNIDENTIFIED → success=true, identified=false, card=null.
        """
        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.return_value = None

        image = _make_jpeg()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['identified'])
        self.assertIsNone(data['card'])
        self.assertIn('message', data)

    @patch('cards.views.ScryfallService')
    @patch('cards.views.VisionService')
    def test_ai_reads_random_text_scryfall_not_found(
        self, MockVision, MockScryfall
    ):
        """
        IA lê texto aleatório que não é carta → Scryfall não encontra
        → Retorno limpo sem erro.
        """
        from cards.services.scryfall_service import ScryfallCardNotFound

        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.return_value = 'random gibberish text'

        mock_scryfall_instance = MockScryfall.return_value
        mock_scryfall_instance.search_card.side_effect = ScryfallCardNotFound(
            'Carta não encontrada'
        )

        image = _make_jpeg()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['identified'])
        self.assertIsNone(data['card'])

    # ─── CENÁRIO 4: Falha de Integração ───

    @patch('cards.views.VisionService')
    def test_vision_api_timeout_returns_503(self, MockVision):
        """
        OpenRouter timeout → 503 Service Unavailable.
        Sistema responde com graceful degradation.
        """
        from cards.services.vision_service import VisionServiceUnavailable

        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.side_effect = VisionServiceUnavailable(
            'Serviço não respondeu a tempo.'
        )

        image = _make_jpeg()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    @patch('cards.views.VisionService')
    def test_vision_api_quota_exceeded_returns_503(self, MockVision):
        """
        OpenRouter 429 (cota esgotada) → 503.
        """
        from cards.services.vision_service import VisionServiceQuotaExceeded

        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.side_effect = VisionServiceQuotaExceeded(
            'Limite atingido.'
        )

        image = _make_jpeg()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch('cards.views.ScryfallService')
    @patch('cards.views.VisionService')
    def test_scryfall_down_returns_503(self, MockVision, MockScryfall):
        """
        Scryfall fora do ar → 503 Service Unavailable.
        Sistema não quebra.
        """
        from cards.services.scryfall_service import ScryfallServiceUnavailable

        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.return_value = MOCK_VISION_SUCCESS

        mock_scryfall_instance = MockScryfall.return_value
        mock_scryfall_instance.search_card.side_effect = ScryfallServiceUnavailable(
            'Scryfall indisponível.'
        )

        image = _make_jpeg()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    # ─── SEGURANÇA: Respostas de erro não expõem detalhes ───

    @patch('cards.views.VisionService')
    def test_error_responses_dont_expose_internals(self, MockVision):
        """
        Respostas de erro NÃO devem conter stack traces,
        nomes de classes internas ou paths do servidor.
        """
        from cards.services.vision_service import VisionServiceUnavailable

        mock_vision_instance = MockVision.return_value
        mock_vision_instance.identify_card.side_effect = VisionServiceUnavailable(
            'Timeout'
        )

        image = _make_jpeg()
        response = self.client.post(ENDPOINT, {'image': image}, format='multipart')

        response_text = response.content.decode()
        # Não deve conter informações internas
        self.assertNotIn('Traceback', response_text)
        self.assertNotIn('File "/', response_text)
        self.assertNotIn('django', response_text.lower().replace('django rest framework', ''))
        self.assertNotIn('openrouter', response_text.lower())

    # ─── GET não permitido ───

    def test_get_method_not_allowed(self):
        """GET no endpoint de identify → 405 Method Not Allowed."""
        response = self.client.get(ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
