# pylint: disable=no-name-in-module
from django.urls import path
from chat.consumers import GroupConsumer, JoinAndLeave, PrivateChatConsumer

websocket_urlpatterns = [
    path("ws/chat_list/", JoinAndLeave.as_asgi()),
    path("ws/groups/<uuid:uuid>/", GroupConsumer.as_asgi()),
    path("ws/chats/<uuid:uuid>/", PrivateChatConsumer.as_asgi()),
]
