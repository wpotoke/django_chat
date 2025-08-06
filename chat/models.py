from datetime import datetime
from uuid import uuid4
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model

from django.urls import reverse

User = get_user_model()


class PrivateChat(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False)
    participants = models.ManyToManyField(User)
    created = models.DateTimeField(auto_now_add=True)
    icon = models.ImageField(
        verbose_name="Иконка чата",
        upload_to="images/icons_chat/%Y/%m/%d",
        default="images/icons_chat/default.png",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=("png", "jpg", "jpeg"))],
    )

    def __str__(self) -> str:
        return f"Chat {self.uuid}"

    def get_absolute_url(self):
        return reverse("private_chat", args=[str(self.uuid)])

    def add_participants(self, user1, user2):
        self.participants.add(user1, user2)
        self.save()


class Group(models.Model):
    """Групповая модель, в которой несколько пользователей могут делиться идеями и обсуждать их"""

    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    members = models.ManyToManyField(User)
    icon = models.ImageField(
        verbose_name="Иконка чата",
        upload_to="images/icons_chat/%Y/%m/%d",
        default="images/icons_chat/default.png",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=("png", "jpg", "jpeg"))],
    )

    def __str__(self) -> str:
        return f"Group {self.name}-{self.uuid}"

    def get_absolute_url(self):
        return reverse("group", args=[str(self.uuid)])

    def add_user_to_group(self, user: User):
        """Вспомогательная функция для добавления пользователя в группу и создания объекта"""
        self.members.add(user)
        self.event_set.create(type="Join", user=user)
        self.save()

    def remove_user_from_group(self, user: User):
        """Функция для удаления членов группы, когда они выходят из группы чата"""
        self.members.remove(user)
        self.event_set.create(type="Left", user=user)
        self.save()


class Message(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    private_chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, blank=True, null=True)
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="Ответ на сообщение",
    )

    def __str__(self) -> str:
        # pylint: disable=no-member
        date = self.timestamp.date()
        time = self.timestamp.time()
        return f"{self.author}:- {self.content} @{date} {time.hour}:{time.minute}"


class Event(models.Model):
    CHOISES = [
        ("Join", "join"),
        ("Left", "left"),
    ]

    type = models.CharField(choices=CHOISES, max_length=10)
    description = models.CharField(help_text="A description of the event that occurred", max_length=50, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.description = f"{self.user.username} {self.type} the {self.group.name} group"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.description}"
