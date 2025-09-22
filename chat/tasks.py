# pylint:disable=broad-exception-caught
from datetime import timedelta
from django.utils import timezone
from django.template import Template, Context
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django_channels_chat.celery import app
from chat.models import Message

REPORT_TEMPLATE = """
Ваша активность за день:
Отправлено сообщений: {{ count_message }}
"""


@app.task
def send_count_messages_per_day():
    today = timezone.now().date()
    start_of_day = timezone.make_aware(timezone.datetime(today.year, today.month, today.day))
    end_of_day = start_of_day + timedelta(days=1)

    for user in get_user_model().objects.filter(is_active=True):
        try:
            messages_today = Message.objects.filter(author=user, timestamp__gte=start_of_day, timestamp__lt=end_of_day)

            count_message = messages_today.count()

            if count_message > 0:
                template = Template(REPORT_TEMPLATE)
                send_mail(
                    "Your Daily Activity Report",
                    template.render(Context({"count_message": count_message})),
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                print(f"Sent report to {user.email}: {count_message} messages")

        except Exception as e:
            print(f"Error sending email to {user.email}: {str(e)}")
