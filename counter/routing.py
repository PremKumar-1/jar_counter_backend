# counter/routing.py

from django.urls import re_path
from .consumers import JarCountConsumer

websocket_urlpatterns = [
    re_path(r'ws/jar-counts/$', JarCountConsumer.as_asgi()),
]
