# pylint: disable=broad-exception-caught, import-outside-toplevel
import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import User
from .models import Event, Message, Group, PrivateChat


class UserDataMixin:
    @database_sync_to_async
    def get_profile_url(self, user):
        if hasattr(user, "profile"):
            return user.profile.get_absolute_url()
        return "#"

    @database_sync_to_async
    def get_user_avatar(self, user):
        if hasattr(user, "profile") and user.profile.avatar:
            return user.profile.avatar.url
        return "/static/images/avatars/default.png"

    @database_sync_to_async
    def get_chat(self, model, uuid):
        return model.objects.get(uuid=uuid)

    @database_sync_to_async
    def create_message(self, type_chat_name, type_chat, user, content, reply_to=None):
        if type_chat_name == "group_chat":
            return Message.objects.create(author=user, content=content, group=type_chat, reply_to=reply_to)
        if type_chat_name == "private_chat":
            return Message.objects.create(author=user, content=content, private_chat=type_chat, reply_to=reply_to)
        return None

    @database_sync_to_async
    def get_replied_message(self, type_chat_name, type_chat, message_id):
        try:
            if type_chat_name == "group_chat":
                return Message.objects.select_related("author").get(id=message_id, group=type_chat)
            if type_chat_name == "private_chat":
                return Message.objects.select_related("author").get(id=message_id, private_chat=type_chat)
            return None
        except (ObjectDoesNotExist, ValueError, TypeError):
            return None


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


class BaseChatConsumer(UserDataMixin):
    ...


class GroupConsumer(UserDataMixin, AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_uuid = None
        self.group = None
        self.user = None

    async def connect(self):
        self.group_uuid = str(self.scope["url_route"]["kwargs"]["uuid"])
        self.user = self.scope["user"]
        try:
            self.group = await super().get_chat(Group, self.group_uuid)
            await self.channel_layer.group_add(self.group_uuid, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            if data.get("type") != "text_message":
                return

            reply_to_id = data.get("reply_to")
            replied_message = None

            if reply_to_id:
                replied_message = await super().get_replied_message(
                    type_chat_name="group_chat", type_chat=self.group, message_id=reply_to_id
                )
                if not replied_message:
                    print(f"Replied message {reply_to_id} not found")

            message = await super().create_message(
                type_chat_name="group_chat",
                type_chat=self.group,
                user=self.user,
                content=data.get("message"),
                reply_to=replied_message,
            )

            message_data = await self.prepare_message_data(message, replied_message)
            await self.channel_layer.group_send(self.group_uuid, message_data)

        except Exception as e:
            print(f"Error in receive: {str(e)}")
            import traceback

            traceback.print_exc()

    async def prepare_message_data(self, message, replied_message):
        avatar_url = await super().get_user_avatar(self.user)
        profile_url = await super().get_profile_url(self.user)

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
            replied_avatar = await super().get_user_avatar(replied_message.author)
            replied_profile_url = await super().get_profile_url(replied_message.author)
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


class PrivateChatConsumer(UserDataMixin, AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.private_chat_uuid = None
        self.private_chat = None
        self.user = None
        self.other_user = None

    async def connect(self):
        self.private_chat_uuid = str(self.scope["url_route"]["kwargs"]["uuid"])
        self.user = self.scope["user"]
        try:
            self.private_chat = await super().get_chat(PrivateChat, self.private_chat_uuid)
            if not await self.is_user_in_chat():
                await self.close()
                return None

            self.other_user = await self.get_other_user()
            await self.channel_layer.group_add(self.private_chat_uuid, self.channel_name)
            await self.accept()

        except Exception as e:
            print(f"Connection error: {str(e)}")
            await self.close()

    @database_sync_to_async
    def is_user_in_chat(self):
        return self.private_chat.participants.exclude(id=self.user.id).exists()

    @database_sync_to_async
    def get_other_user(self):
        return self.private_chat.participants.exclude(id=self.user.id).first()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            if data.get("type") != "text_message":
                return

            reply_to_id = data.get("reply_to")
            replied_message = None
            if reply_to_id:
                replied_message = await super().get_replied_message(
                    type_chat_name="private_chat", type_chat=self.private_chat, message_id=reply_to_id
                )

            message = await super().create_message(
                type_chat_name="private_chat",
                type_chat=self.private_chat,
                user=self.user,
                content=data.get("message"),
                reply_to=replied_message,
            )

            message_data = await self.prepare_message_data(message, replied_message)
            await self.channel_layer.group_send(self.private_chat_uuid, message_data)

        except Exception as e:
            print(f"Error in receive: {str(e)}")
            import traceback

            traceback.print_exc()

    async def prepare_message_data(self, message, replied_message=None):
        avatar_url = await super().get_user_avatar(self.user)
        profile_url = await super().get_profile_url(self.user)

        message_data = {
            "type": "private_message",
            "id": message.id,
            "content": message.content,
            "username": self.user.username,
            "avatar": avatar_url,
            "timestamp": str(message.timestamp),
            "profile_url": profile_url,
            "is_own": True,
        }

        if replied_message:
            replied_avatar = await super().get_user_avatar(replied_message.author)
            replied_profile_url = await super().get_profile_url(replied_message.author)
            message_data["reply_to"] = {
                "id": replied_message.id,
                "username": replied_message.author.username,
                "content": replied_message.content,
                "avatar": replied_avatar,
                "profile_url": replied_profile_url,
            }

        return message_data

    async def private_message(self, event):
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
