from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Event


@receiver(post_save, sender=Event)
def broadcast_event_to_groups(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    group_uuid = str(instance.group.uuid)
    event_message = str(instance)
    async_to_sync(channel_layer.group_send)(
        group_uuid,
        {"type": "text_message", "message": event_message, "status": instance.type, "user": str(instance.user)},
    )
