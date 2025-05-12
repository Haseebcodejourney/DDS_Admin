from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DDS.settings')

app = Celery('DDS')
@app.task
def test_task():
    print("[🔥 CELERY TEST TASK] It works!")
    return "Celery is working fine"

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task
def debug_task(self):
    print(f"[🐛 CELERY DEBUG] Task {self.request!r}")

@app.task
def test_task():
    print("[🔥 CELERY TEST TASK] It works!")
    return "Celery is working fine"
