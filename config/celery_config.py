import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from logging import getLogger


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("YummyYard")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    broker_connection_retry_on_startup=True,
)