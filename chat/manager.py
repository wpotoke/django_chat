from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PrivateChatManager(models.Manager):
    def get_or_create_chat(self, user1, user2):
        # Сортируем ID пользователей для однозначности
        user_ids = sorted([user1.id, user2.id])

        # Пытаемся найти чат с точно такими участниками
        chat = self.filter(participants__id=user_ids[0]).filter(participants__id=user_ids[1]).distinct().first()

        if chat:
            return chat, False  # Чат найден, не создавался новый

        # Создаем новый чат
        chat = self.create()
        chat.participants.add(user1, user2)
        return chat, True
