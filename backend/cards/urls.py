"""
MTG Translator — URLs do app cards
"""
from django.urls import path
from .views import CardIdentifyView

app_name = 'cards'

urlpatterns = [
    path('identify/', CardIdentifyView.as_view(), name='identify'),
]
