from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import CheckoutSession, StatusType


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
            status=StatusType.DRAFT,
        ).update(status=StatusType.CANCELLED)

        checkout_session = CheckoutSession.objects.create(
            user=user,
            cart=cart,
            farm=farm,
            status=StatusType.DRAFT,
        )
        return checkout_session

    @classmethod
    @transaction.atomic
    def freeze_and_finilize_session(cls, checkout_session: CheckoutSession):

        if checkout_session.status != StatusType.DRAFT:
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

        checkout_session.status = StatusType.AWAITING_PAYMENT
        checkout_session.payment_deadline_at = timezone.now() + timezone.timedelta(
            minutes=30
        )
        checkout_session.save()

        return checkout_session
