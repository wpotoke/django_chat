# pylint: disable=broad-exception-caught,no-member,attribute-defined-outside-init
import json
import traceback
from typing import Any, Dict

from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from accounts.models import User
from .models import Event, Message, Group, PrivateChat


class UserDataMixin:
    """Миксин для работы с пользовательскими данными"""

    @database_sync_to_async
    def get_profile_url(self, user: User) -> str:
        return user.profile.get_absolute_url() if hasattr(user, "profile") else "#"

    @database_sync_to_async
    def get_user_avatar(self, user: User) -> str:
        if hasattr(user, "profile") and user.profile.avatar:
            return user.profile.avatar.url
        return "/static/images/avatars/default.png"


class ChatOperationsMixin:
    """Миксин для операций с чатами"""

    @database_sync_to_async
    def get_chat(self, model: Any, uuid: str) -> Any:
        return model.objects.get(uuid=uuid)

    @database_sync_to_async
    def create_message(self, chat_type: str, chat_obj: Any, user: User, content: str, reply_to: Any = None) -> Message:
        message_data = {
            "author": user,
            "content": content,
            "reply_to": reply_to,
        }

        # Устанавливаем правильное поле в зависимости от типа чата
        if chat_type == "group":
            message_data["group"] = chat_obj
        else:
            message_data["private_chat"] = chat_obj

        return Message.objects.create(**message_data)

    @database_sync_to_async
    def get_replied_message(self, chat_type: str, chat_obj: Any, message_id: int) -> Message:
        try:
            return Message.objects.select_related("author").get(id=message_id, **{chat_type: chat_obj})
        except (ObjectDoesNotExist, ValueError, TypeError):
            return None


class BaseChatConsumer(UserDataMixin, ChatOperationsMixin):
    """Базовый класс для чатов с общими методами"""

    async def handle_connect(self: AsyncWebsocketConsumer, model: Any, chat_attr: str) -> None:
        """Обработка подключения к чату"""
        try:
            self.user = self.scope["user"]
            uuid = str(self.scope["url_route"]["kwargs"]["uuid"])
            setattr(self, f"{chat_attr}_uuid", uuid)

            chat = await self.get_chat(model, uuid)
            setattr(self, chat_attr, chat)

            if hasattr(self, "validate_connection"):
                if not await self.validate_connection():
                    await self.close()
                    return

            await self.channel_layer.group_add(uuid, self.channel_name)
            await self.accept()
        except Exception as e:
            print(f"Connection error: {str(e)}")
            traceback.print_exc()
            await self.close()

    async def handle_receive(
        self: AsyncWebsocketConsumer, chat_type: str, chat_attr: str, text_data: str = None
    ) -> None:
        """Обработка входящих сообщений"""
        try:
            data = json.loads(text_data)
            if data.get("type") != "text_message":
                return

            if chat_type not in ["group", "private_chat"]:
                raise ValueError(f"Invalid chat type: {chat_type}")

            reply_to_id = data.get("reply_to")
            replied_message = None

            if reply_to_id:
                replied_message = await self.get_replied_message(
                    chat_type=chat_type, chat_obj=getattr(self, chat_attr), message_id=reply_to_id
                )
                if not replied_message:
                    print(f"Replied message {reply_to_id} not found")

            message = await self.create_message(
                chat_type=chat_type,
                chat_obj=getattr(self, chat_attr),
                user=self.user,
                content=data.get("message"),
                reply_to=replied_message,
            )

            message_data = await self.prepare_message_data(message, replied_message)
            await self.channel_layer.group_send(getattr(self, f"{chat_attr}_uuid"), message_data)

        except Exception as e:
            print(f"Error in receive: {str(e)}")
            traceback.print_exc()

    async def prepare_message_data(self, message: Message, replied_message: Message = None) -> Dict[str, Any]:
        """Подготовка данных сообщения для отправки"""
        avatar_url = await self.get_user_avatar(self.user)
        profile_url = await self.get_profile_url(self.user)

        message_data = {
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

    async def send_message_response(self, event: Dict[str, Any]) -> None:
        """Отправка сообщения клиенту"""
        try:
            response_data = {k: v for k, v in event.items() if k not in ["type", "sender_id"]}
            response_data["is_own"] = self.user.username == event["username"]

            if event.get("reply_to"):
                response_data["reply_to"] = event["reply_to"]

            await self.send(text_data=json.dumps(response_data))
        except Exception as e:
            print(f"Error sending message: {str(e)}")


class JoinAndLeave(WebsocketConsumer):
    """Обработчик подключения/отключения от групп"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def connect(self) -> None:
        self.user = self.scope["user"]
        self.accept()

    def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:
        try:
            data = json.loads(text_data)
            handler = getattr(self, data.get("type", ""), None)
            if handler and callable(handler):
                handler(data.get("data"))
        except json.JSONDecodeError:
            print("Invalid JSON data received")

    def leave_group(self, group_uuid: str) -> None:
        group = Group.objects.get(uuid=group_uuid)
        group.remove_user_from_group(self.user)
        self._send_response("leave_group", group_uuid)

    def join_group(self, group_uuid: str) -> None:
        group = Group.objects.get(uuid=group_uuid)
        group.add_user_to_group(self.user)
        self._send_response("join_group", group_uuid)

    def _send_response(self, response_type: str, data: Any) -> None:
        self.send(json.dumps({"type": response_type, "data": data}))


class GroupConsumer(BaseChatConsumer, AsyncWebsocketConsumer):
    """Consumer для группового чата"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_uuid = None
        self.group = None
        self.user = None

    async def connect(self) -> None:
        await self.handle_connect(model=Group, chat_attr="group")

    async def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:
        await self.handle_receive("group", "group", text_data=text_data)

    async def prepare_message_data(self, message: Message, replied_message: Message = None) -> Dict[str, Any]:
        message_data = await super().prepare_message_data(message, replied_message)
        message_data["type"] = "chat_message"
        return message_data

    async def chat_message(self, event: Dict[str, Any]) -> None:
        await self.send_message_response(event)


class PrivateChatConsumer(BaseChatConsumer, AsyncWebsocketConsumer):
    """Consumer для приватного чата"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.other_user = None

    async def connect(self) -> None:
        await self.handle_connect(model=PrivateChat, chat_attr="private_chat")

    async def validate_connection(self) -> bool:
        return await self.is_user_in_chat()

    @database_sync_to_async
    def is_user_in_chat(self) -> bool:
        return self.private_chat.participants.filter(id=self.user.id).exists()

    @database_sync_to_async
    def get_other_user(self) -> User:
        return self.private_chat.participants.exclude(id=self.user.id).first()

    async def receive(self, text_data: str = None, bytes_data: bytes = None) -> None:
        await self.handle_receive("private_chat", "private_chat", text_data=text_data)

    async def prepare_message_data(self, message: Message, replied_message: Message = None) -> Dict[str, Any]:
        message_data = await super().prepare_message_data(message, replied_message)
        message_data["type"] = "private_message"
        return message_data

    async def private_message(self, event: Dict[str, Any]) -> None:
        await self.send_message_response(event)


class CallConsumer(AsyncWebsocketConsumer):
    """Обработка WebRTC-звонков через WebSocket"""

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"call_{self.room_name}"
        self.peer_id = None

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            if data.get("type") == "register":
                self.data.get("peer_id")
                return None

            # Пересылаем сигнал всем в комнате (кроме отправителя)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "webrtc_signal",
                    "data": data,
                    "sender_channel": self.channel_name,
                },
            )
        except Exception as e:
            print(f"Call error: {str(e)}")
            traceback.print_exc()

    async def webrtc_signal(self, event):
        """Отправка сигналов WebRTC (SDP, ICE кандидаты)"""
        if self.channel_name != event["sender_channel"]:  # Исключаем отправителя
            await self.send(text_data=json.dumps(event["data"]))
