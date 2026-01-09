import os

from celery import Celery

from user.tasks import flush_invalid_tokens


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airport_service.settings")

app = Celery("airport_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        45.0,
        flush_invalid_tokens.s(),
        name="flush invalid refresh tokens every 45 seconds",
    )
