from celery import shared_task
from django.utils import timezone
from .models import StatusType, CheckoutSession


@shared_task(name="checkout.tasks.expire_abandoned_checkout_sessions")
def expire_abandoned_checkout_sessions():

    now = timezone.now()

    expired_sessions = CheckoutSession.objects.filter(
        status=StatusType.AWAITING_PAYMENT,
        payment_deadline_at__lte=now,
    )

    count = expired_sessions.count()

    if count:
        expired_sessions.update(
            status=StatusType.EXPIRED,
        )
        return "updated all the expired checkout sessions."

    return "no expired session found."
