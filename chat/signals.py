from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Event


@receiver(post_save, sender=Event)
def broadcast_event_to_groups(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        str(instance.group.uuid),
        {
            "type": "chat_message",  # Важно: тот же тип обработчика
            "content": str(instance),
            "username": instance.user.username,
            "status": "Join" if instance.type == "Join" else "Left",
            "timestamp": str(instance.timestamp),
            "message_type": "event",
        },
    )
