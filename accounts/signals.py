from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from accounts.tasks import send_verification_email

User = get_user_model()


@receiver(post_save, sender=User)
def user_update(sender, instance, *args, **kwagrs):
    if not instance.is_verified:
        send_verification_email.delay(instance.pk)
