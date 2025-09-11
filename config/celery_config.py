import os
from django.conf import settings
from celery import Celery
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

app = Celery("YummyYard")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# app.conf.update(
    # broker_connection_retry_on_startup=True,
# )