from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
 

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chat_websocket_urlpatterns 
        )
    ),
})
