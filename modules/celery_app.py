from modules import create_app
from modules.tasks import scheduler_test
from modules.celery_utils import celery_init_app
from celery.schedules import crontab
import time


app = create_app()
celery = celery_init_app(app)

celery.conf.beat_schedule = {
    'run-every-minute': {
        'task': 'scheduler_test',
        'schedule': crontab(minute='*/1'),
        'options': {'queue': 'scheduled_task'}
    }
}

print("Beat schedule:", celery.conf.beat_schedule)