# pylint: disable=broad-exception-caught, import-outside-toplevel
import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
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
        self.user = self.scope["user"]
        try:
            self.group = await self.get_group()
            await self.channel_layer.group_add(self.group_uuid, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await self.close()

    @database_sync_to_async
    def get_group(self):
        return Group.objects.get(uuid=self.group_uuid)

    @database_sync_to_async
    def create_message(self, content, reply_to=None):
        return Message.objects.create(author=self.user, content=content, group=self.group, reply_to=reply_to)

    @database_sync_to_async
    def get_user_avatar(self, user):
        if hasattr(user, "profile") and user.profile.avatar:
            return user.profile.avatar.url
        return "/static/images/avatars/default.png"

    @database_sync_to_async
    def get_profile_url(self, user):
        if hasattr(user, "profile"):
            return user.profile.get_absolute_url()
        return "#"

    @database_sync_to_async
    def get_replied_message(self, message_id):
        try:
            return Message.objects.select_related("author").get(id=message_id)
        except (ObjectDoesNotExist, ValueError, TypeError):
            return None

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            if data.get("type") != "text_message":
                return

            reply_to_id = data.get("reply_to")
            replied_message = None

            if reply_to_id:
                replied_message = await self.get_replied_message(reply_to_id)
                if not replied_message:
                    print(f"Replied message {reply_to_id} not found")

            message = await self.create_message(content=data.get("message"), reply_to=replied_message)

            message_data = await self.prepare_message_data(message, replied_message)
            await self.channel_layer.group_send(self.group_uuid, message_data)

        except Exception as e:
            print(f"Error in receive: {str(e)}")
            import traceback

            traceback.print_exc()

    async def prepare_message_data(self, message, replied_message):
        avatar_url = await self.get_user_avatar(self.user)
        profile_url = await self.get_profile_url(self.user)

        message_data = {
            "type": "chat_message",
            "id": message.id,
            "content": message.content,
            "username": self.user.username,
            "avatar": avatar_url,
            "timestamp": str(message.timestamp),
            "profile_url": profile_url,
            "is_own": True,
        }

        if replied_message:
            replied_avatar = await self.get_user_avatar(replied_message.author)
            replied_profile_url = await self.get_profile_url(replied_message.author)
            message_data["reply_to"] = {
                "id": replied_message.id,
                "username": replied_message.author.username,
                "content": replied_message.content,
                "avatar": replied_avatar,
                "profile_url": replied_profile_url,
            }

        return message_data

    async def chat_message(self, event):
        try:
            response_data = {
                "id": event["id"],
                "content": event["content"],
                "username": event["username"],
                "timestamp": event["timestamp"],
                "avatar": event["avatar"],
                "profile_url": event["profile_url"],
                "is_own": self.user.username == event["username"],
            }

            if event.get("reply_to"):
                response_data["reply_to"] = event["reply_to"]

            await self.send(text_data=json.dumps(response_data))
        except Exception as e:
            print(f"Error in chat_message: {str(e)}")
