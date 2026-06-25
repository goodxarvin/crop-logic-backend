from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from order.models import Order
from order.models import StatusType as OrderStatusType
from .models import CheckoutSession
from .models import StatusType as SessionStatusType


class CheckoutService:

    @classmethod
    @transaction.atomic
    def create_checkout_session(cls, user, farm=None):

        cart = user.cart
        available_cart_items = cart.cart_items.exists()
        if not available_cart_items:
            return ValidationError("threse is nothing in the cart of this user.")

        CheckoutSession.objects.filter(
            user=user,
            status=SessionStatusType.DRAFT,
        ).update(status=SessionStatusType.CANCELLED)

        checkout_session = CheckoutSession.objects.create(
            user=user,
            cart=cart,
            farm=farm,
            status=SessionStatusType.DRAFT,
        )
        return checkout_session

    @classmethod
    @transaction.atomic
    def freeze_and_finilize_session(cls, checkout_session: CheckoutSession) -> tuple:

        if checkout_session.status != SessionStatusType.DRAFT:
            raise ValidationError("checkout status type must be draft.")

        requirements = checkout_session.get_requirements

        if requirements["requires_shipping_address"]:
            if not checkout_session.shipping_address:
                raise ValidationError("shipping address required")

            shipping_address = checkout_session.shipping_address
            checkout_session.shipping_address_snapshot = {
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
            if not checkout_session.farm_address:
                raise ValidationError("farm address required.")

            farm_address = checkout_session.farm_address
            checkout_session.farm_address_snapshot = {
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

        checkout_cart = checkout_session.cart
        checkout_session.pricing_snapshot = {
            "total_items_count": checkout_cart.total_items_count,
            "total_items_base_price": checkout_cart.total_items_base_price,
            "total_items_discount_price": checkout_cart.total_items_discount_price,
            "total_items_price": checkout_cart.total_items_price,
        }

        checkout_session.status = SessionStatusType.AWAITING_PAYMENT
        checkout_session.payment_deadline_at = timezone.now() + timezone.timedelta(
            minutes=30
        )
        checkout_session.save()

        items_list = []
        for item in checkout_cart.cart_items.all():
            items_list.append(
                {
                    "sku_id": item.sku.id,
                    "sku_title": item.sku.title,
                    "quantity": item.quantity,
                    "farm_id": item.farm.uuid if item.farm else None,
                    "base_price": item.total_sku_base_price,
                    "discount_amount": item.total_sku_discount_amount,
                    "final_price": item.final_sku_price,
                }
            )

        Order.objects.create(
            user=checkout_session.user,
            checkout_session_uuid=checkout_session.uuid,
            total_amount=checkout_cart.total_items_price,
            status=OrderStatusType.PENDING,
            shipping_address_snapshot=(
                checkout_session.shipping_address_snapshot
                if checkout_session.shipping_address_snapshot
                else {}
            ),
            farm_address_snapshot=(
                checkout_session.farm_address_snapshot
                if checkout_session.farm_address_snapshot
                else {}
            ),
            items_snapshot={"items": items_list},
        )

        return checkout_session
