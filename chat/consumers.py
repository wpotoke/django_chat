import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from accounts.models import User
from .models import Event, Message, Group


class JoinAndLeave(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def connect(self):
        self.user = self.scope["user"]
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        type_event = text_data.get("type", None)
        data = text_data.get("data", None)

        if type_event == "leave_group":
            self.leave_group(data)
        elif type_event == "join_group":
            self.join_group(data)

    def leave_group(self, group_uuid):
        group = Group.objects.get(uuid=group_uuid)
        group.remove_user_from_group(self.user)
        data = {"type": "leave_group", "data": group_uuid}
        self.send(json.dumps(data))

    def join_group(self, group_uuid):
        group = Group.objects.get(uuid=group_uuid)
        group.add_user_to_group(self.user)
        data = {"type": "join_group", "data": group_uuid}
        self.send(json.dumps(data))


class GroupConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_uuid = None
        self.group = None
        self.user = None

    async def connect(self):
        self.group_uuid = str(self.scope["url_route"]["kwargs"]["uuid"])
        self.group = await database_sync_to_async(Group.objects.get)(uuid=self.group_uuid)
        await self.channel_layer.group_add(self.group_uuid, self.channel_name)

        self.user = self.scope["user"]
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        type_event = text_data.get("type", None)
        message_content = text_data.get("message", None)

        if type_event == "text_message":
            # Создаем сообщение в БД
            message = await database_sync_to_async(Message.objects.create)(
                author=self.user, content=message_content, group=self.group
            )

            # Отправляем сообщение в группу
            await self.channel_layer.group_send(
                self.group_uuid,
                {
                    "type": "chat_message",  # Это указывает на метод обработчика
                    "content": message.content,
                    "username": self.user.username,
                    "timestamp": str(message.timestamp),
                    "message_type": "user_message",
                },
            )

    async def chat_message(self, event):
        # Формируем данные для отправки клиенту
        response_data = {
            "message": event.get("content", ""),
            "username": event.get("username", ""),
            "timestamp": event.get("timestamp", ""),
            "is_own": (self.user.username == event.get("username", None)),
        }

        # Добавляем статус для событий Join/Left
        if event.get("status"):
            response_data["status"] = event["status"]

        await self.send(text_data=json.dumps(response_data))
