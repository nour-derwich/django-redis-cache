"""
Celery configuration for Redis Caching Demo.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Warm product cache every 5 minutes
    'warm-product-cache': {
        'task': 'products.tasks.warm_product_cache',
        'schedule': crontab(minute='*/5'),
    },
    # Clear expired cache entries every hour
    'cleanup-expired-cache': {
        'task': 'products.tasks.cleanup_expired_cache',
        'schedule': crontab(minute=0, hour='*/1'),
    },
    # Generate cache statistics every 15 minutes
    'generate-cache-stats': {
        'task': 'products.tasks.generate_cache_statistics',
        'schedule': crontab(minute='*/15'),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')