"""
MTG Translator — Serializers

Serializers para validação de entrada (upload de imagem)
e formatação de saída (dados da carta identificada).
"""
from rest_framework import serializers


class CardIdentifyRequestSerializer(serializers.Serializer):
    """
    Serializer de entrada para o endpoint de identificação.

    Valida que uma imagem foi enviada no campo 'image'.
    A validação detalhada (MIME type, tamanho, etc.) é feita
    pelo validators.py para separação de responsabilidades.
    """
    image = serializers.ImageField(
        required=True,
        help_text='Foto da carta MTG (JPEG ou PNG, máx. 5MB)',
    )


class CardDataSerializer(serializers.Serializer):
    """
    Serializer de saída com os dados da carta identificada.
    Representa a estrutura de dados retornada pelo Scryfall.
    """
    name_en = serializers.CharField(help_text='Nome em inglês')
    name_pt = serializers.CharField(
        help_text='Nome em português', allow_blank=True
    )
    type = serializers.CharField(help_text='Tipo da carta')
    mana_cost = serializers.CharField(
        help_text='Custo de mana', allow_blank=True
    )
    oracle_text = serializers.CharField(
        help_text='Texto do oráculo (EN)', allow_blank=True
    )
    oracle_text_pt = serializers.CharField(
        help_text='Texto do oráculo (PT)', allow_blank=True
    )
    image_url = serializers.URLField(
        help_text='URL da imagem em alta resolução'
    )
    scryfall_url = serializers.URLField(
        help_text='URL da página no Scryfall'
    )
    set_name = serializers.CharField(
        help_text='Nome da edição/coleção'
    )
    rarity = serializers.CharField(
        help_text='Raridade da carta'
    )


class CardIdentifyResponseSerializer(serializers.Serializer):
    """
    Serializer da resposta completa do endpoint de identificação.
    """
    success = serializers.BooleanField(
        help_text='Se a operação foi bem-sucedida'
    )
    identified = serializers.BooleanField(
        help_text='Se a carta foi identificada pela IA'
    )
    card = CardDataSerializer(
        required=False, allow_null=True,
        help_text='Dados da carta (null se não identificada)'
    )
    message = serializers.CharField(
        required=False, allow_blank=True,
        help_text='Mensagem informativa'
    )
