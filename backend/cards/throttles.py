"""
MTG Translator — Throttles (Rate Limiting)

Protege os endpoints críticos contra abuso e ataques DoS.
Limita requisições por IP para controlar custos com APIs pagas.
"""
from rest_framework.throttling import AnonRateThrottle


class CardIdentifyThrottle(AnonRateThrottle):
    """
    Limita requisições de identificação de carta por IP.
    Padrão: 10 requisições por minuto.
    Configurável via settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['card_identify']
    """
    scope = 'card_identify'


class CardIdentifyBurstThrottle(AnonRateThrottle):
    """
    Limite de burst para identificação de carta por IP.
    Padrão: 3 requisições por segundo.
    Evita rajadas de requisições automatizadas.
    """
    scope = 'card_identify_burst'
