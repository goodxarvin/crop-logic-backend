from celery import shared_task
from django.utils import timezone
from .models import Order, StatusType


@shared_task(name="order.tasks.cancel_order_after_3_days")
def cancel_order_after_3_days():

    three_days_ago = timezone.now() - timezone.timedelta(days=3)

    expired_orders = Order.objects.filter(
        created_at__lte=three_days_ago,
        status=StatusType.PENDING,
    )

    count = expired_orders.count()

    if count:
        expired_orders.update(
            status=StatusType.CANCELLED,
        )
        return "cancelled every expired order."

    return "no expired orders found."
