from django.contrib import admin
from .models import CardScan


@admin.register(CardScan)
class CardScanAdmin(admin.ModelAdmin):
    """Admin para visualizar scans realizados."""

    list_display = [
        'id', 'identified', 'card_name_en', 'card_name_pt', 'created_at'
    ]
    list_filter = ['identified', 'created_at']
    search_fields = ['card_name_en', 'card_name_pt', 'scryfall_id']
    readonly_fields = ['created_at', 'raw_ai_response']
    ordering = ['-created_at']
