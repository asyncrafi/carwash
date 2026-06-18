import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.local')

# This must come BEFORE importing anything that touches Django models
django_asgi_app = get_asgi_application()

# Only import routing AFTER Django is set up
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.messages.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.messages.routing.websocket_urlpatterns
        )
    ),
})  