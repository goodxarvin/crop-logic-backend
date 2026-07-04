from celery import shared_task
from order.models import Order
from .services import ProvisioningService
import logging

logger = logging.getLogger(__name__)


@shared_task(name="provisioning.tasks.create_and_run_pending_tasks")
def create_and_run_pending_tasks(order_uuid: str):
    try:
        order = Order.objects.filter(uuid=order_uuid).first()
        ProvisioningService.create_task_from_order(order=order)
        ProvisioningService.run_pending_tasks()
        return "Provisioning tasks created and ran successfully."

    except Order.DoesNotExist:
        logger.error(f"Order with uuid {order_uuid} does not exist.")
        return f"Order with uuid {order_uuid} does not exist."
    except Exception as e:
        logger.error(
            f"Error creating and running provisioning tasks for order {order.uuid}: {str(e)}"
        )
        return f"Error: {str(e)}"
