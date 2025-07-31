# pylint: disable=broad-exception-caught
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
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.group_uuid, self.channel_name)
        await self.accept()

    @database_sync_to_async
    def get_group(self):
        return Group.objects.filter(uuid=self.group_uuid)

    @database_sync_to_async
    def create_message(self, content):
        return Message.objects.create(author=self.user, content=content, group=self.group)

    @database_sync_to_async
    def get_user_avatar(self, user):
        return user.profile.avatar.url if hasattr(user, "profile") and user.profile.avatar else None

    @database_sync_to_async
    def get_profile_url(self, user):
        if hasattr(user, "profile"):
            return user.profile.get_absolute_url()
        return "#"

    async def receive(self, text_data=None, bytes_data=None):
        try:
            text_data = json.loads(text_data)
            type_event = text_data.get("type")
            message_content = text_data.get("message")

            if type_event == "text_message":
                message = await database_sync_to_async(Message.objects.create)(
                    author=self.user, content=message_content, group=self.group
                )
                avatar_url = await self.get_user_avatar(self.user) or "static/images/avatars/default.png"
                profile_url = await self.get_profile_url(self.user)

                await self.channel_layer.group_send(
                    self.group_uuid,
                    {
                        "type": "chat_message",
                        "content": message.content,
                        "username": self.user.username,
                        "avatar": avatar_url,
                        "timestamp": str(message.timestamp),
                        "profile_url": profile_url,
                        "message_type": "user_message",
                    },
                )
        except Exception as e:
            print(f"Error in receive: {e}")

    async def chat_message(self, event):
        try:
            response_data = {
                "message": event.get("content", ""),
                "username": event.get("username", ""),
                "timestamp": event.get("timestamp", ""),
                "avatar": event.get("avatar", ""),
                "profile_url": event.get("profile_url", ""),
                "is_own": (self.user.username == event.get("username", "")),
            }

            if event.get("status"):
                response_data["status"] = event["status"]

            await self.send(text_data=json.dumps(response_data))
        except Exception as e:
            print(f"Error in chat_message: {e}")
