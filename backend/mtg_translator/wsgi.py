"""
WSGI config for mtg_translator project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mtg_translator.settings')
application = get_wsgi_application()
