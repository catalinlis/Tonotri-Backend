from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TonotriBackend.settings')

app = Celery('TonotriBackend')

# Only settings starting with: 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto discover tasks in Django apps
# It tells Celery to automatically search every Django app in:
# INSTALLED_APPS
# and import app_name.tasks
app.autodiscover_tasks()

# This defines a Celery task directly in the config file (usually just for testing).
# bind=True - gives the task access to its 
# own instance: self.request
# So you can inspect metadata:
# task id
# retries
# arguments
# worker info
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')