# pylint: disable=no-name-in-module
from django.urls import path
from chat.consumers import GroupConsumer, JoinAndLeave, PrivateChatConsumer, CallConsumer

websocket_urlpatterns = [
    path("", JoinAndLeave.as_asgi()),
    path("ws/groups/<uuid:uuid>/", GroupConsumer.as_asgi()),
    path("ws/chats/<uuid:uuid>/", PrivateChatConsumer.as_asgi()),
    path("ws/call/<uuid:room_name>/", CallConsumer.as_asgi()),
]
