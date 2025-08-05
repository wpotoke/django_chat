from django.contrib import admin
from chat.models import PrivateChat, Group, Message, Event


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ["uuid", "name"]


@admin.register(PrivateChat)
class PrivateChatAdmin(admin.ModelAdmin):
    list_display = ["uuid"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["author", "content"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["type", "user"]
