"""
ASGI config for jar_counter project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

# jar_counter/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from jar_counter import routing
import counter.routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jar_counter.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            counter.routing.websocket_urlpatterns
        )
    ),
})