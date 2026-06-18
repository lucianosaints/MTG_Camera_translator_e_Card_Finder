"""
MTG Translator — URLs raiz
"""
from django.contrib import admin
from django.http import HttpResponse, FileResponse
from django.views.static import serve
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
import os

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from cards.views import RegisterView

def download_apk(request):
    """Força o download do arquivo APK."""
    apk_path = settings.BASE_DIR / 'dist' / 'app.apk'
    if os.path.exists(apk_path):
        response = FileResponse(open(apk_path, 'rb'), content_type='application/vnd.android.package-archive')
        response['Content-Disposition'] = 'attachment; filename="mtg-translator.apk"'
        return response
    return HttpResponse("APK ainda não foi gerado/disponibilizado.", status=404)

urlpatterns = [
    
    path('admin/', admin.site.urls),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/register/', RegisterView.as_view(), name='register'),
    path('api/v1/cards/', include('cards.urls')),
    path('download/app.apk', download_apk, name='download_apk'),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

def render_react(request):
    """
    Catch-all view que serve o index.html do React.
    Agora ele procura a pasta 'dist' dentro do próprio backend!
    """
    index_path = settings.BASE_DIR / 'dist' / 'index.html'
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())
    except FileNotFoundError:
        return HttpResponse(
            "Frontend build não encontrado. Verifique se copiou a pasta 'dist' para o backend!", 
            status=501
        )

# 1. Via expressa para os arquivos visuais (CSS/JS) do React passarem direto
urlpatterns.append(re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'dist' / 'assets'}))

# 2. Via expressa para os arquivos do PWA (Service Worker, Manifest) na raiz do dist
urlpatterns.append(re_path(r'^(?P<path>(manifest\.webmanifest|sw\.js|registerSW\.js|workbox-.*\.js|icones\.png))$', serve, {'document_root': settings.BASE_DIR / 'dist'}))

# 3. O Leão de Chácara (Catch-all) para o index.html - TEM QUE FICAR POR ÚLTIMO!
urlpatterns.append(re_path(r'^.*$', render_react, name='react_frontend'))
