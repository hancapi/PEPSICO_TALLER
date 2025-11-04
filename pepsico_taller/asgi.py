#pepsico_taller/pepsico_taller/asgi.py
"""
ASGI config for pepsico_taller project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pepsico_taller.settings')

application = get_asgi_application()
