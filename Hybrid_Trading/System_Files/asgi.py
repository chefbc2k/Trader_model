import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import Hybrid_Trading.System_Files.routing  # Correct import for routing

# Set the default settings module for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hybrid_Trading.System_Files.settings')

# Initialize the ASGI application for both HTTP and WebSocket protocols
application = ProtocolTypeRouter({
    # This handles HTTP requests
    "http": get_asgi_application(),

    # This handles WebSocket requests
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                Hybrid_Trading.System_Files.routing.websocket_urlpatterns  # Correct WebSocket routing
            )
        )
    ),
})