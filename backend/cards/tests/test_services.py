"""
MTG Translator — Testes dos Serviços (Vision + Scryfall)

REGRA: Todas as chamadas a APIs externas são MOCKADAS.
Nenhuma requisição real é feita durante os testes.

Cenários cobertos:
- VisionService: sucesso, carta não identificada, timeout, 429, 500
- ScryfallService: sucesso, carta não encontrada, timeout, 500
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from cards.services.vision_service import (
    VisionService,
    VisionServiceError,
    VisionServiceUnavailable,
    VisionServiceQuotaExceeded,
)
from cards.services.scryfall_service import (
    ScryfallService,
    ScryfallCardNotFound,
    ScryfallServiceUnavailable,
)


# ─────────────────────────────────────────────
# MOCK DATA — Respostas simuladas das APIs
# ─────────────────────────────────────────────

MOCK_OPENROUTER_SUCCESS = {
    'choices': [
        {
            'message': {
                'content': 'Lightning Bolt',
            },
        },
    ],
}

MOCK_OPENROUTER_UNIDENTIFIED = {
    'choices': [
        {
            'message': {
                'content': 'UNIDENTIFIED',
            },
        },
    ],
}

MOCK_SCRYFALL_CARD = {
    'id': '12345-abcde',
    'name': 'Lightning Bolt',
    'type_line': 'Instant',
    'mana_cost': '{R}',
    'oracle_text': 'Lightning Bolt deals 3 damage to any target.',
    'set_name': 'Alpha',
    'rarity': 'common',
    'scryfall_uri': 'https://scryfall.com/card/lea/161/lightning-bolt',
    'image_uris': {
        'small': 'https://cards.scryfall.io/small/front/l/bolt.jpg',
        'normal': 'https://cards.scryfall.io/normal/front/l/bolt.jpg',
        'large': 'https://cards.scryfall.io/large/front/l/bolt.jpg',
    },
}

MOCK_SCRYFALL_PT = {
    'data': [
        {
            'name': 'Lightning Bolt',
            'printed_name': 'Relâmpago',
            'printed_text': 'Relâmpago causa 3 pontos de dano em qualquer alvo.',
        },
    ],
}

MOCK_SCRYFALL_NOT_FOUND = {
    'object': 'error',
    'code': 'not_found',
    'details': 'No cards found matching "random gibberish"',
}

FAKE_IMAGE_BYTES = b'\xff\xd8\xff\xe0' + b'\x00' * 100


# ─────────────────────────────────────────────
# TESTES — VisionService
# ─────────────────────────────────────────────

@override_settings(
    OPENROUTER_API_KEY='sk-test-fake-key',
    OPENROUTER_MODEL='test/model',
)
class TestVisionService(TestCase):
    """Testes para o serviço de IA de Visão (OpenRouter)."""

    @patch('cards.services.vision_service.requests.post')
    def test_identify_card_success(self, mock_post):
        """IA identifica carta com sucesso → retorna nome."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_OPENROUTER_SUCCESS
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        service = VisionService()
        result = service.identify_card(FAKE_IMAGE_BYTES)

        self.assertEqual(result, 'Lightning Bolt')
        mock_post.assert_called_once()

    @patch('cards.services.vision_service.requests.post')
    def test_identify_card_unidentified(self, mock_post):
        """IA não consegue identificar → retorna None."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_OPENROUTER_UNIDENTIFIED
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        service = VisionService()
        result = service.identify_card(FAKE_IMAGE_BYTES)

        self.assertIsNone(result)

    @patch('cards.services.vision_service.requests.post')
    def test_identify_card_empty_response(self, mock_post):
        """IA retorna resposta vazia → retorna None."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'choices': [{'message': {'content': ''}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        service = VisionService()
        result = service.identify_card(FAKE_IMAGE_BYTES)

        self.assertIsNone(result)

    @patch('cards.services.vision_service.requests.post')
    def test_timeout_raises_unavailable(self, mock_post):
        """Timeout na API → VisionServiceUnavailable."""
        import requests as req
        mock_post.side_effect = req.exceptions.Timeout('Connection timed out')

        service = VisionService()
        with self.assertRaises(VisionServiceUnavailable):
            service.identify_card(FAKE_IMAGE_BYTES)

    @patch('cards.services.vision_service.requests.post')
    def test_connection_error_raises_unavailable(self, mock_post):
        """Falha de conexão → VisionServiceUnavailable."""
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError('DNS failure')

        service = VisionService()
        with self.assertRaises(VisionServiceUnavailable):
            service.identify_card(FAKE_IMAGE_BYTES)

    @patch('cards.services.vision_service.requests.post')
    def test_429_raises_quota_exceeded(self, mock_post):
        """API retorna 429 → VisionServiceQuotaExceeded."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response

        service = VisionService()
        with self.assertRaises(VisionServiceQuotaExceeded):
            service.identify_card(FAKE_IMAGE_BYTES)

    @patch('cards.services.vision_service.requests.post')
    def test_500_raises_unavailable(self, mock_post):
        """API retorna 500 → VisionServiceUnavailable."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        service = VisionService()
        with self.assertRaises(VisionServiceUnavailable):
            service.identify_card(FAKE_IMAGE_BYTES)

    @override_settings(OPENROUTER_API_KEY='')
    def test_missing_api_key_raises(self):
        """API key não configurada → VisionServiceError."""
        with self.assertRaises(VisionServiceError):
            VisionService()


# ─────────────────────────────────────────────
# TESTES — ScryfallService
# ─────────────────────────────────────────────

class TestScryfallService(TestCase):
    """Testes para o serviço Scryfall."""

    @patch('cards.services.scryfall_service.requests.get')
    def test_search_card_success(self, mock_get):
        """Busca por carta existente → retorna dados estruturados."""
        # Mock das duas chamadas: busca EN + busca PT
        mock_response_en = MagicMock()
        mock_response_en.status_code = 200
        mock_response_en.json.return_value = MOCK_SCRYFALL_CARD
        mock_response_en.raise_for_status.return_value = None

        mock_response_pt = MagicMock()
        mock_response_pt.status_code = 200
        mock_response_pt.json.return_value = MOCK_SCRYFALL_PT

        mock_get.side_effect = [mock_response_en, mock_response_pt]

        service = ScryfallService()
        # Reset rate limit para testes
        ScryfallService._last_request_time = 0
        result = service.search_card('Lightning Bolt')

        self.assertEqual(result['name_en'], 'Lightning Bolt')
        self.assertEqual(result['name_pt'], 'Relâmpago')
        self.assertEqual(result['mana_cost'], '{R}')
        self.assertEqual(result['rarity'], 'common')
        self.assertIn('scryfall.io', result['image_url'])
        self.assertEqual(result['scryfall_id'], '12345-abcde')

    @patch('cards.services.scryfall_service.requests.get')
    def test_search_card_not_found(self, mock_get):
        """Carta inexistente → ScryfallCardNotFound."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = MOCK_SCRYFALL_NOT_FOUND
        mock_get.return_value = mock_response

        service = ScryfallService()
        ScryfallService._last_request_time = 0

        with self.assertRaises(ScryfallCardNotFound):
            service.search_card('random gibberish text')

    @patch('cards.services.scryfall_service.requests.get')
    def test_search_card_server_error(self, mock_get):
        """Scryfall retorna 500 → ScryfallServiceUnavailable."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        service = ScryfallService()
        ScryfallService._last_request_time = 0

        with self.assertRaises(ScryfallServiceUnavailable):
            service.search_card('Lightning Bolt')

    @patch('cards.services.scryfall_service.requests.get')
    def test_search_card_timeout(self, mock_get):
        """Timeout no Scryfall → ScryfallServiceUnavailable."""
        import requests as req
        mock_get.side_effect = req.exceptions.Timeout('Timeout')

        service = ScryfallService()
        ScryfallService._last_request_time = 0

        with self.assertRaises(ScryfallServiceUnavailable):
            service.search_card('Lightning Bolt')

    @patch('cards.services.scryfall_service.requests.get')
    def test_search_card_connection_error(self, mock_get):
        """Falha de conexão com Scryfall → ScryfallServiceUnavailable."""
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError('No route')

        service = ScryfallService()
        ScryfallService._last_request_time = 0

        with self.assertRaises(ScryfallServiceUnavailable):
            service.search_card('Lightning Bolt')

    @patch('cards.services.scryfall_service.requests.get')
    def test_search_card_without_pt_translation(self, mock_get):
        """Carta sem tradução PT → retorna dados sem PT preenchido."""
        mock_response_en = MagicMock()
        mock_response_en.status_code = 200
        mock_response_en.json.return_value = MOCK_SCRYFALL_CARD
        mock_response_en.raise_for_status.return_value = None

        # Busca PT retorna 404
        mock_response_pt = MagicMock()
        mock_response_pt.status_code = 404

        mock_get.side_effect = [mock_response_en, mock_response_pt]

        service = ScryfallService()
        ScryfallService._last_request_time = 0
        result = service.search_card('Lightning Bolt')

        self.assertEqual(result['name_en'], 'Lightning Bolt')
        self.assertEqual(result['name_pt'], '')  # Sem tradução
        self.assertEqual(result['oracle_text_pt'], '')

    @patch('cards.services.scryfall_service.requests.get')
    def test_build_response_extracts_best_image(self, mock_get):
        """Resposta deve extrair a imagem de melhor resolução disponível."""
        card_data_large = MOCK_SCRYFALL_CARD.copy()
        mock_response_en = MagicMock()
        mock_response_en.status_code = 200
        mock_response_en.json.return_value = card_data_large
        mock_response_en.raise_for_status.return_value = None

        mock_response_pt = MagicMock()
        mock_response_pt.status_code = 404

        mock_get.side_effect = [mock_response_en, mock_response_pt]

        service = ScryfallService()
        ScryfallService._last_request_time = 0
        result = service.search_card('Lightning Bolt')

        # Deve pegar 'large' quando disponível
        self.assertIn('large', result['image_url'])
