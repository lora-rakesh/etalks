"""
ASGI config for project project.
 
It exposes the ASGI callable as a module-level variable named ``application``.
 
For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""
 # project/asgi.py
import os
from channels.routing import get_default_application
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django_asgi_app = get_asgi_application()

import app.routing

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            app.routing.websocket_urlpatterns
        )
    ),
})
