import os
from celery import Celery
from celery.beat import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_channels_chat.settings")
app = Celery(
    "publish",
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
)

app.config_from_object("django.conf:settings")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "send-report-every-day": {
        "task": "chat.tasks.send-report-every-single-minute",
        "schedule": crontab(hour=23, minute=58),
    }
}
