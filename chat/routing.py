# pylint: disable=no-name-in-module
from django.urls import path
from chat.consumers import GroupConsumer, JoinAndLeave, PrivateChatConsumer

websocket_urlpatterns = [
    path("", JoinAndLeave.as_asgi()),
    path("groups/<uuid:uuid>/", GroupConsumer.as_asgi()),
    path("chats/<uuid:uuid>/", PrivateChatConsumer.as_asgi()),
]
