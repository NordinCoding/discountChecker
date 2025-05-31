from modules import create_app
from modules.celery_utils import celery_init_app

app = create_app()
celery = celery_init_app(app)