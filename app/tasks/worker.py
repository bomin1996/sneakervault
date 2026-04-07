from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sneakervault",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    beat_schedule={
        "collect-market-prices": {
            "task": "app.tasks.price_tasks.collect_market_prices",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
        "generate-daily-report": {
            "task": "app.tasks.price_tasks.generate_daily_price_report",
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM KST
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
