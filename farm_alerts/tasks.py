import logging

from celery import shared_task

from .services import sync_all_farm_alert_trackers

logger = logging.getLogger("farm_alerts")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def sync_farm_alert_trackers(self):
    logger.info("farm alerts periodic sync task started task_id=%s", getattr(self.request, "id", ""))
    result = sync_all_farm_alert_trackers()
    logger.info("farm alerts periodic sync task finished result=%s", result)
    return result
