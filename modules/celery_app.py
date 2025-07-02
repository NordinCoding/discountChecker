from modules import create_app
from modules.tasks import scheduled_rescrape
from modules.celery_utils import celery_init_app
from celery.schedules import crontab
import time


app = create_app()
celery = celery_init_app(app)

celery.conf.beat_schedule = {
    'run-every-tuesday-at-3am': {
        'task': 'scheduled_rescrape',
        'schedule': crontab(hour=3, minute=0, day_of_week=2),
        'options': {'queue': 'scheduled_task'}
    }
}

print("Beat schedule:", celery.conf.beat_schedule)