"""
MTG Translator — Serviço Scryfall

Responsável por buscar dados oficiais de cartas na API pública do Scryfall.
Extrai imagem HD, nome traduzido (PT-BR), texto do oráculo e metadados.

Referência da API: https://scryfall.com/docs/api

Segurança:
- Scryfall é API pública, sem chave necessária
- Respeita rate limit (50-100ms entre requests)
- Timeout configurável
"""
import logging
import time
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger('cards')

# Timeout para chamadas à API (conexão, leitura)
REQUEST_TIMEOUT = (5, 15)


class ScryfallServiceError(Exception):
    """Erro genérico do serviço Scryfall."""
    pass


class ScryfallServiceUnavailable(ScryfallServiceError):
    """API do Scryfall indisponível."""
    pass


class ScryfallCardNotFound(ScryfallServiceError):
    """Carta não encontrada no Scryfall."""
    pass


class ScryfallService:
    """
    Serviço de integração com a API do Scryfall.

    Busca dados de cartas MTG pelo nome, extraindo informações
    traduzidas quando disponíveis.
    """

    # Timestamp da última requisição (para respeitar rate limit)
    _last_request_time: float = 0.0
    _MIN_INTERVAL: float = 0.1  # 100ms entre requests

    def __init__(self):
        self.base_url: str = getattr(
            settings, 'SCRYFALL_API_BASE', 'https://api.scryfall.com'
        )

    def _respect_rate_limit(self) -> None:
        """Aguarda intervalo mínimo entre requisições ao Scryfall."""
        elapsed = time.time() - ScryfallService._last_request_time
        if elapsed < self._MIN_INTERVAL:
            time.sleep(self._MIN_INTERVAL - elapsed)
        ScryfallService._last_request_time = time.time()

    def search_card(self, card_name: str) -> dict:
        """
        Busca uma carta pelo nome na API do Scryfall.

        Usa busca fuzzy para tolerar erros de OCR/identificação.
        Tenta buscar a versão em português quando disponível.

        Args:
            card_name: Nome da carta em inglês (identificado pela IA)

        Returns:
            Dicionário com dados estruturados da carta:
            {
                'name_en': str,
                'name_pt': str,
                'type': str,
                'mana_cost': str,
                'oracle_text': str,
                'oracle_text_pt': str,
                'image_url': str,
                'scryfall_url': str,
                'set_name': str,
                'rarity': str,
                'scryfall_id': str,
            }

        Raises:
            ScryfallCardNotFound: Se a carta não for encontrada
            ScryfallServiceUnavailable: Se o Scryfall estiver fora do ar
        """
        # Primeiro: buscar carta em inglês
        card_data = self._fetch_card(card_name)

        # Segundo: tentar buscar tradução em português
        pt_data = self._fetch_card_pt(card_name)

        # Montar resposta estruturada
        result = self._build_response(card_data, pt_data)

        logger.info(
            'Carta encontrada: %s (%s)',
            result.get('name_en'), result.get('set_name')
        )

        return result

    def _fetch_card(self, card_name: str) -> dict:
        """
        Busca os dados da carta em inglês via fuzzy search.

        Args:
            card_name: Nome da carta

        Returns:
            Dados brutos do Scryfall

        Raises:
            ScryfallCardNotFound: Carta não encontrada
            ScryfallServiceUnavailable: Scryfall indisponível
        """
        self._respect_rate_limit()

        url = f'{self.base_url}/cards/named'
        params = {'fuzzy': card_name}

        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={'Accept': 'application/json', 'User-Agent': 'MTG-Translator/1.0'},
            )

            if response.status_code == 404:
                logger.info('Carta não encontrada no Scryfall: "%s"', card_name)
                raise ScryfallCardNotFound(
                    f'A carta "{card_name}" não foi encontrada no banco de dados.'
                )

            if response.status_code >= 500:
                logger.error(
                    'Erro no servidor Scryfall: %s', response.status_code
                )
                raise ScryfallServiceUnavailable(
                    'O serviço de dados de cartas está temporariamente indisponível.'
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error('Timeout ao comunicar com Scryfall')
            raise ScryfallServiceUnavailable(
                'O serviço de dados de cartas não respondeu a tempo.'
            )

        except requests.exceptions.ConnectionError:
            logger.error('Falha de conexão com Scryfall')
            raise ScryfallServiceUnavailable(
                'Não foi possível conectar ao serviço de dados de cartas.'
            )

        except (ScryfallCardNotFound, ScryfallServiceUnavailable):
            raise

        except Exception as exc:
            logger.exception('Erro inesperado no ScryfallService: %s', exc)
            raise ScryfallServiceError(
                'Erro interno ao buscar dados da carta.'
            )

    def _fetch_card_pt(self, card_name: str) -> Optional[dict]:
        """
        Tenta buscar a versão em português da carta via API de busca.

        Args:
            card_name: Nome da carta em inglês

        Returns:
            Dados brutos do Scryfall com tradução, ou None se não encontrar
        """
        self._respect_rate_limit()

        url = f'{self.base_url}/cards/search'
        params = {
            'q': f'name:"{card_name}" lang:pt',
            'unique': 'prints',
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={'Accept': 'application/json', 'User-Agent': 'MTG-Translator/1.0'},
            )

            if response.status_code != 200:
                logger.debug(
                    'Tradução PT não encontrada para: "%s"', card_name
                )
                return None

            data = response.json()
            cards = data.get('data', [])
            return cards[0] if cards else None

        except Exception as exc:
            # Falha na busca de tradução não é crítica
            logger.debug(
                'Falha ao buscar tradução PT para "%s": %s',
                card_name, exc
            )
            return None

    def _build_response(
        self, card_data: dict, pt_data: Optional[dict]
    ) -> dict:
        """
        Monta a resposta estruturada combinando dados EN e PT.

        Args:
            card_data: Dados da carta em inglês
            pt_data: Dados da carta em português (pode ser None)

        Returns:
            Dicionário estruturado com todos os dados da carta
        """
        # Extrair imagem de alta resolução
        image_uris = card_data.get('image_uris', {})
        image_url = (
            image_uris.get('large')
            or image_uris.get('normal')
            or image_uris.get('small', '')
        )

        # Extrair nome e texto em português
        name_pt = ''
        oracle_text_pt = ''

        # Primeiro: verificar se a carta EN já tem printed_name (algumas edições)
        if card_data.get('printed_name'):
            name_pt = card_data['printed_name']

        if card_data.get('printed_text'):
            oracle_text_pt = card_data['printed_text']

        # Segundo: sobrescrever com dados da busca PT se disponíveis
        if pt_data:
            name_pt = pt_data.get('printed_name', '') or pt_data.get('name', name_pt)
            oracle_text_pt = (
                pt_data.get('printed_text', '')
                or pt_data.get('oracle_text', oracle_text_pt)
            )
            
            # Tratamento para cartas Dupla-Face em Português
            if not oracle_text_pt and 'card_faces' in pt_data:
                faces_pt = []
                for face in pt_data['card_faces']:
                    f_name = face.get('printed_name', face.get('name', ''))
                    f_text = face.get('printed_text', face.get('oracle_text', ''))
                    faces_pt.append(f"// {f_name} //\n{f_text}")
                oracle_text_pt = "\n\n".join(faces_pt)

        oracle_text_en = card_data.get('oracle_text', '')
        
        # Tratamento para cartas Dupla-Face em Inglês
        if not oracle_text_en and 'card_faces' in card_data:
            faces_en = []
            for face in card_data['card_faces']:
                f_name = face.get('name', '')
                f_text = face.get('oracle_text', '')
                faces_en.append(f"// {f_name} //\n{f_text}")
            oracle_text_en = "\n\n".join(faces_en)
        
        # Terceiro: Se ainda não tiver tradução, usar IA como Fallback!
        if oracle_text_en and not oracle_text_pt:
            try:
                # Import dinâmico para evitar dependência circular caso exista
                from cards.services.vision_service import VisionService
                vision = VisionService()
                logger.info('Sem tradução oficial no Scryfall. Utilizando IA de fallback.')
                oracle_text_pt = vision.translate_text(oracle_text_en)
                
                # Se não tem nome em PT, podemos tentar manter o original ou pedir pra IA
                # Por simplicidade e segurança, o nome geralmente é mantido em EN se não há tradução oficial
                if not name_pt:
                    name_pt = card_data.get('name', '')
            except Exception as e:
                logger.warning('Falha no fallback de tradução por IA: %s', e)

        return {
            'name_en': card_data.get('name', ''),
            'name_pt': name_pt,
            'type': card_data.get('type_line', ''),
            'mana_cost': card_data.get('mana_cost', ''),
            'oracle_text': oracle_text_en,
            'oracle_text_pt': oracle_text_pt,
            'image_url': image_url,
            'scryfall_url': card_data.get('scryfall_uri', ''),
            'set_name': card_data.get('set_name', ''),
            'rarity': card_data.get('rarity', ''),
            'scryfall_id': card_data.get('id', ''),
        }
