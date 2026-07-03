import logging
from django.db import transaction
from django.utils import timezone
from access_control.services import build_farm_access_profile
from commerce_catalog.models import SKU
from order.models import Order
from order.models import StatusType as OrderStatusType
from commerce_catalog.models import ItemType
from subscriptions.models import SubscriptionPlan
from .models import ProvisioningStaus, ProvisioningTask, ProvisioningType

logger = logging.getLogger(__name__)


class ProvisioningService:

    @classmethod
    @transaction.atomic
    def create_task_from_order(cls, order: Order):

        if order.status != OrderStatusType.PAID:
            raise ValueError("order must be paid")

        items_snapshot_data = order.items_snapshot or {}
        items = items_snapshot_data.get("items", [])

        for item in items:

            logger.info(
                f"--------------------------------------------Processing item: {str(item)} --- {type(item)}"
            )
            sku_id = item.get("sku_id", None)
            if not sku_id:
                continue
            sku = SKU.objects.select_related("item").get(pk=sku_id)
            sellable_item_type = sku.item.item_type

            logger.info(
                f"--------------------------------------------item id : {sku.item.external_id} - {sku.code} - {sku.item.item_type} - {sku.item.title} - {sku.item.is_active}"
            )

            if sellable_item_type == ItemType.SUBSCRIPTION_PALN:

                try:

                    sellable_item_subscription_plan = SubscriptionPlan.objects.filter(
                        uuid=sku.item.external_id,
                        is_active=True,
                    ).first()

                    ProvisioningTask.objects.create(
                        user=order.user,
                        order=order,
                        farm_id=getattr(order.farm, "pk", None),
                        task_type=ProvisioningType.SUBSCRIPTION,
                        status=ProvisioningStaus.PENDING,
                        metadata={
                            "plan_uuid": str(sellable_item_subscription_plan.uuid),
                            "duration_days": sellable_item_subscription_plan.duration_days,
                        },
                    )

                except Exception as e:
                    logger.error(
                        f"Error creating provisioning task for order {order.uuid}: {str(e)}"
                    )
                    raise e

            elif sellable_item_type == ItemType.PHYSICAL_DEVICE:

                try:
                    ProvisioningTask.objects.create(
                        user=order.user,
                        order=order,
                        farm_id=getattr(order.farm, "farm_uuid", None),
                        task_type=ProvisioningType.DEVICE,
                        status=ProvisioningStaus.PENDING,
                        metadata={
                            "sku_uuid": sku.id,
                            "quantity": item.get("quantity", 1),
                        },
                    )

                except Exception as e:
                    logger.error(
                        f"Error creating provisioning task for order {order.uuid}: {str(e)}"
                    )
                    raise e

    @classmethod
    @transaction.atomic
    def run_pending_tasks(cls):
        pending_tasks = ProvisioningTask.objects.select_for_update().filter(
            status=ProvisioningStaus.PENDING
        )

        for task in pending_tasks:

            task.status = ProvisioningStaus.PROCESING
            task.save(update_fields=["status"])

            try:
                if task.task_type == ProvisioningType.SUBSCRIPTION:
                    cls._provision_subscription(task)
                elif task.task_type == ProvisioningType.DEVICE:
                    # cls._provision_device(task)
                    pass

                task.status = ProvisioningStaus.SUCCESSFUL
                task.save(update_fields=["status"])

            except Exception as e:
                logger.error(f"Error provisioning task {task.uuid}: {str(e)}")
                task.status = ProvisioningStaus.FAILED
                task.metadata["error_log"] = str(e)
                task.save(update_fields=["status", "metadata"])

    @classmethod
    def _provision_subscription(cls, task: ProvisioningTask):

        from farm_hub.models import FarmHub

        farm_id = task.farm_id
        plan_id = task.metadata.get("plan_uuid")
        duration_days = task.metadata.get("duration_days", 365)

        farm = FarmHub.objects.select_for_update().filter(farm_uuid=farm_id).first()
        plan = SubscriptionPlan.objects.filter(uuid=plan_id).first()

        farm.subscription_plan = plan
        farm.subscription_expiry = timezone.now() + timezone.timedelta(
            days=duration_days
        )
        build_farm_access_profile(farm=farm)
        farm.save(update_fields=["subscription_plan", "subscription_expiry"])
