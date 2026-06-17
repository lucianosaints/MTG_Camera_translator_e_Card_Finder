"""
MTG Translator — Tratamento Seguro de Exceções

Handler customizado que garante que erros internos NUNCA
exponham stack traces ou detalhes do servidor ao cliente.
Todos os detalhes vão para os logs internos.
"""
import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('cards')


def custom_exception_handler(exc, context):
    """
    Handler de exceções customizado para o DRF.

    - Erros de validação (400): retorna detalhes amigáveis
    - Throttling (429): retorna mensagem de rate limit
    - Erros internos (500): retorna mensagem genérica,
      loga detalhes internamente

    Args:
        exc: Exceção capturada
        context: Contexto da requisição

    Returns:
        Response com erro formatado de forma segura
    """
    # Deixa o DRF processar exceções conhecidas primeiro
    response = exception_handler(exc, context)

    if response is not None:
        # Formatar resposta de erro de forma consistente
        custom_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': _get_friendly_message(response),
            },
        }
        response.data = custom_data
        return response

    # Exceções não tratadas pelo DRF (500 Internal Server Error)
    # Log detalhado internamente, mensagem genérica ao cliente
    view = context.get('view', None)
    view_name = view.__class__.__name__ if view else 'Unknown'

    logger.exception(
        'Erro não tratado em %s: %s — %s',
        view_name, type(exc).__name__, str(exc)
    )

    return Response(
        {
            'success': False,
            'error': {
                'code': 500,
                'message': (
                    'Ocorreu um erro interno no servidor. '
                    'Tente novamente mais tarde.'
                ),
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_friendly_message(response) -> str:
    """
    Extrai uma mensagem amigável da resposta de erro do DRF.

    Args:
        response: Response do DRF com dados de erro

    Returns:
        String com mensagem amigável para o cliente
    """
    data = response.data

    # Throttling (429)
    if response.status_code == 429:
        return 'Muitas requisições. Aguarde um momento antes de tentar novamente.'

    # Erro de validação com detalhes por campo
    if isinstance(data, dict):
        messages = []
        for field, errors in data.items():
            if isinstance(errors, list):
                messages.extend(str(e) for e in errors)
            elif isinstance(errors, str):
                messages.append(errors)
            elif isinstance(errors, dict):
                # Erros aninhados
                for sub_errors in errors.values():
                    if isinstance(sub_errors, list):
                        messages.extend(str(e) for e in sub_errors)
        if messages:
            return ' '.join(messages)

    # Lista de erros
    if isinstance(data, list):
        return ' '.join(str(e) for e in data)

    # Fallback
    return str(data) if data else 'Erro desconhecido.'
