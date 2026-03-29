from celery import shared_task
from django.db import transaction

from .services import analyze_and_store_zone_soil_data


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def process_zone_soil_data(self, zone_id):
    with transaction.atomic():
        analyze_and_store_zone_soil_data(zone_id=zone_id)
    return {"zone_id": zone_id, "status": "processed"}
