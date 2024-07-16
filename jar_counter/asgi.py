"""
ASGI config for jar_counter project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# jar_counter/asgi.py

# asgi.py

import os
from django.core.asgi import get_asgi_application
from jar_counter.routing import application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jar_counter.settings')

django_asgi_app = get_asgi_application()

application = application


