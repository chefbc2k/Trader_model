# Hybrid_Trading/System_Files/asgi.py

import os
import django

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# 1. Set the default settings module for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hybrid_Trading.System_Files.settings')

# 2. Setup Django
django.setup()

# 3. Import routing after Django setup
import Hybrid_Trading.System_Files.routing

# 4. Initialize the ASGI application for both HTTP and WebSocket protocols
application = ProtocolTypeRouter({
    # This handles HTTP requests
    "http": get_asgi_application(),

    # This handles WebSocket requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Hybrid_Trading.System_Files.routing.websocket_urlpatterns
        )
    ),
})