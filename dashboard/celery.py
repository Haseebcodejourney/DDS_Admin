import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DDS.settings')  # Update if your settings module is different

app = Celery('dashboard')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
