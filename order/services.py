from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from checkout.models import StatusType as SessionStatusType
from checkout.models import CheckoutSession
from .models import StatusType as OrderStatusType
from .models import Order


class OrderService:

    @classmethod
    @transaction.atomic
    def create_order(cls, user, farm=None):

        cart = user.cart
        available_cart_items = cart.cart_items.exists()
        if not available_cart_items:
            return ValidationError("threse is nothing in the cart of this user.")

        order = Order.objects.create(
            user=user,
            cart=cart,
            farm=farm,
            status=OrderStatusType.PENDING,
        )
        return order

    @classmethod
    @transaction.atomic
    def freeze_and_finilize_order(cls, order: Order) -> tuple:

        # if order.status != OrderStatusType.PENDING:
        #     raise ValidationError("order status type must be pending.")

        requirements = order.get_requirements

        if requirements["requires_shipping_address"]:
            if not order.shipping_address:
                raise ValidationError("shipping address required")

            shipping_address = order.shipping_address
            order.shipping_address_snapshot = {
                "address_type": shipping_address.address_type,
                "receiver_name": shipping_address.receiver_name,
                "province": shipping_address.province,
                "city": shipping_address.city,
                "postal_code": shipping_address.postal_code,
                "address_detail": shipping_address.postal_code,
                "created_at": shipping_address.created_at,
                "updated_at": shipping_address.updated_at,
            }

        if requirements["requires_farm_address"]:
            if not order.farm_address:
                raise ValidationError("farm address required.")

            farm_address = order.farm_address
            order.farm_address_snapshot = {
                "address_type": farm_address.address_type,
                "receiver_name": farm_address.receiver_name,
                "receiver_phone": farm_address.receiver_phone,
                "latitute": farm_address.latitute,
                "longtitute": farm_address.longtitute,
                "for_sensor": farm_address.for_sensor,
                "province": farm_address.province,
                "city": farm_address.city,
                "postal_code": farm_address.postal_code,
                "address_detail": farm_address.postal_code,
                "created_at": farm_address.created_at,
                "updated_at": farm_address.updated_at,
            }

        order_cart = order.cart
        order.pricing_snapshot = {
            "total_items_count": order_cart.total_items_count,
            "total_items_base_price": order_cart.total_items_base_price,
            "total_items_discount_price": order_cart.total_items_discount_price,
            "total_items_price": order_cart.total_items_price,
        }

        items_list = []
        for item in order_cart.cart_items.all():
            items_list.append(
                {
                    "sku_id": item.sku.id,
                    "sku_title": item.sku.title,
                    "quantity": item.quantity,
                    "farm_id": item.farm.id if item.farm else None,
                    "base_price": item.total_sku_base_price,
                    "discount_amount": item.total_sku_discount_amount,
                    "final_price": item.final_sku_price,
                }
            )

        order.items_snapshot = {"items": items_list}
        order.save()

        CheckoutSession.objects.filter(
            user=order.user,
            status=SessionStatusType.AWAITING_PAYMENT,
        ).update(status=OrderStatusType.CANCELLED)

        CheckoutSession.objects.create(
            user=order.user,
            order_uuid=order.uuid,
            status=SessionStatusType.AWAITING_PAYMENT,
            total_amount=order_cart.total_items_price,
            shipping_address_snapshot=(
                order.shipping_address_snapshot
                if order.shipping_address_snapshot
                else {}
            ),
            farm_address_snapshot=(
                order.farm_address_snapshot if order.farm_address_snapshot else {}
            ),
            items_snapshot={"items": items_list},
            payment_deadline_at=timezone.now() + timezone.timedelta(minutes=30),
        )

        return order
