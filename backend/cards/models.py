"""
MTG Translator — Modelos de Dados

CardScan: Registra cada scan realizado pelo usuário para auditoria
e análise de uso do sistema.
"""
from django.db import models


class CardScan(models.Model):
    """
    Log de cada tentativa de identificação de carta.
    Armazena a imagem original, resultado da identificação
    e metadados da carta encontrada.
    """

    original_image = models.ImageField(
        upload_to='scans/%Y/%m/%d/',
        verbose_name='Imagem Original',
        help_text='Foto da carta enviada pelo usuário',
    )
    card_name_en = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Nome (EN)',
        help_text='Nome da carta em inglês identificado pela IA',
    )
    card_name_pt = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Nome (PT)',
        help_text='Nome da carta traduzido para português',
    )
    scryfall_id = models.CharField(
        max_length=64,
        blank=True,
        default='',
        verbose_name='Scryfall ID',
        help_text='ID único da carta na base do Scryfall',
    )
    identified = models.BooleanField(
        default=False,
        verbose_name='Identificada?',
        help_text='Se a carta foi identificada com sucesso',
    )
    raw_ai_response = models.TextField(
        blank=True,
        default='',
        verbose_name='Resposta Bruta da IA',
        help_text='Texto completo retornado pela IA de visão (debug)',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data do Scan',
    )

    class Meta:
        verbose_name = 'Scan de Carta'
        verbose_name_plural = 'Scans de Cartas'
        ordering = ['-created_at']

    def __str__(self) -> str:
        status = '✓' if self.identified else '✗'
        name = self.card_name_pt or self.card_name_en or 'Não identificada'
        return f'[{status}] {name} — {self.created_at:%d/%m/%Y %H:%M}'
