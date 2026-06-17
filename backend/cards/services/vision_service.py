"""
MTG Translator — Serviço de Visão (OpenRouter)

Responsável por enviar a imagem da carta para a API de IA de Visão
e extrair o nome da carta identificada.

Segurança:
- Chave de API carregada de variável de ambiente
- Timeout configurável para evitar travamento
- Tratamento de erros sem exposição de detalhes internos
"""
import base64
import logging
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger('cards')

# Timeout para chamadas à API (conexão, leitura)
REQUEST_TIMEOUT = (10, 30)


class VisionServiceError(Exception):
    """Erro genérico do serviço de visão."""
    pass


class VisionServiceUnavailable(VisionServiceError):
    """API de visão indisponível (timeout, 5xx, etc.)."""
    pass


class VisionServiceQuotaExceeded(VisionServiceError):
    """Cota da API de visão esgotada (429)."""
    pass


class VisionService:
    """
    Serviço de integração com API de Visão via OpenRouter.

    Envia uma imagem de carta MTG em base64 para um modelo de IA
    com capacidade de visão e retorna o nome da carta identificada.
    """

    API_URL = 'https://openrouter.ai/api/v1/chat/completions'

    # Prompt engenhado para extração precisa do nome da carta
    SYSTEM_PROMPT = (
        "You are a Magic: The Gathering card identification expert. "
        "When shown an image of an MTG card, you must identify the card "
        "and respond with ONLY the card's English name, nothing else. "
        "No quotes, no explanation, no punctuation — just the card name. "
        "If the image is not an MTG card or you cannot identify it, "
        "respond with exactly: UNIDENTIFIED"
    )

    USER_PROMPT = (
        "Identify this Magic: The Gathering card. "
        "Respond with ONLY the English card name."
    )

    def __init__(self):
        self.api_key: str = settings.OPENROUTER_API_KEY
        self.model: str = settings.OPENROUTER_MODEL

        if not self.api_key:
            logger.error('OPENROUTER_API_KEY não configurada no .env')
            raise VisionServiceError(
                'Serviço de IA não configurado. '
                'Contate o administrador do sistema.'
            )

    def identify_card(self, image_bytes: bytes, content_type: str = 'image/jpeg') -> Optional[str]:
        """
        Identifica uma carta MTG a partir dos bytes da imagem.

        Args:
            image_bytes: Conteúdo binário da imagem (JPEG ou PNG)
            content_type: MIME type da imagem

        Returns:
            Nome da carta em inglês, ou None se não identificada

        Raises:
            VisionServiceUnavailable: Se a API estiver fora do ar
            VisionServiceQuotaExceeded: Se a cota da API estiver esgotada
            VisionServiceError: Outros erros inesperados
        """
        # Converter imagem para base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f'data:{content_type};base64,{image_b64}'

        # Montar payload para a API
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': self.SYSTEM_PROMPT,
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': self.USER_PROMPT,
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': data_uri,
                            },
                        },
                    ],
                },
            ],
            'max_tokens': 100,
            'temperature': 0.1,  # Baixa temperatura para respostas consistentes
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://mtg-translator.local',
            'X-Title': 'MTG Camera Translator',
        }

        try:
            logger.info('Enviando imagem para IA de visão (modelo: %s)', self.model)
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            # Verificar código de status
            if response.status_code == 401:
                logger.error('Erro 401: Chave de API do OpenRouter inválida ou não configurada corretamente.')
                raise VisionServiceError(
                    'Configuração do servidor incorreta. Verifique a chave da API de visão.'
                )

            if response.status_code == 429:
                logger.warning('Cota da API OpenRouter esgotada (429)')
                raise VisionServiceQuotaExceeded(
                    'Limite de uso da IA atingido. Tente novamente em alguns minutos.'
                )

            if response.status_code >= 500:
                logger.error(
                    'Erro no servidor OpenRouter: %s — %s',
                    response.status_code, response.text[:200]
                )
                raise VisionServiceUnavailable(
                    'Serviço de IA temporariamente indisponível.'
                )

            response.raise_for_status()

            # Extrair o texto da resposta
            data = response.json()
            card_name = (
                data.get('choices', [{}])[0]
                .get('message', {})
                .get('content', '')
                .strip()
            )

            logger.info('IA retornou: "%s"', card_name)

            # Verificar se a carta foi identificada
            if not card_name or card_name.upper() == 'UNIDENTIFIED':
                logger.info('Carta não identificada pela IA')
                return None

            return card_name

        except requests.exceptions.Timeout:
            logger.error('Timeout ao comunicar com OpenRouter')
            raise VisionServiceUnavailable(
                'Serviço de IA não respondeu a tempo. Tente novamente.'
            )

        except requests.exceptions.ConnectionError:
            logger.error('Falha de conexão com OpenRouter')
            raise VisionServiceUnavailable(
                'Não foi possível conectar ao serviço de IA.'
            )

        except (VisionServiceQuotaExceeded, VisionServiceUnavailable):
            raise  # Re-raise exceções conhecidas

        except Exception as exc:
            logger.exception('Erro inesperado no VisionService: %s', exc)
            raise VisionServiceError(
                'Erro interno ao processar a imagem.'
            )

    def translate_text(self, text: str) -> str:
        """
        Traduz um texto (oracle text de uma carta) do inglês para o português
        utilizando a IA. Usado como fallback quando o Scryfall não possui a versão PT.

        Args:
            text: Texto do oráculo em inglês.

        Returns:
            Texto traduzido para o português.
        """
        if not text:
            return ""

        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        "Você é um tradutor especializado no jogo Magic: The Gathering. "
                        "Sua tarefa é traduzir o texto de regras (Oracle Text) do inglês para o "
                        "português do Brasil, utilizando a terminologia oficial do jogo "
                        "(ex: 'Haste' -> 'Ímpeto', 'Trample' -> 'Atropelar', 'Graveyard' -> 'Cemitério'). "
                        "Responda APENAS com a tradução, sem adicionar aspas, comentários ou explicações."
                    )
                },
                {
                    'role': 'user',
                    'content': text
                }
            ],
            'max_tokens': 500,
            'temperature': 0.1,
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://mtg-translator.local',
            'X-Title': 'MTG Camera Translator',
        }

        try:
            logger.info('Solicitando tradução de fallback para IA')
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()
            translation = (
                data.get('choices', [{}])[0]
                .get('message', {})
                .get('content', '')
                .strip()
            )
            
            # Remover aspas se a IA insistir em colocar
            if translation.startswith('"') and translation.endswith('"'):
                translation = translation[1:-1]
                
            return translation

        except Exception as exc:
            logger.error('Falha ao traduzir texto via IA: %s', exc)
            return text  # Retorna o original em inglês em caso de falha
