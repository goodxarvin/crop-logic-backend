from rest_framework import serializers
from ..models import CheckoutSession


class CheckoutSessionSerializer(serializers.ModelSerializer):

    class Meta:
        model = CheckoutSession
        fields = [
            "uuid",
            "order_uuid",
            "total_amount",
            "status",
            "total_amount",
            "shipping_address_snapshot",
            "farm_address_snapshot",
            "items_snapshot",
            "payment_deadline_at",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InitiateCheckoutSerializer(serializers.Serializer):
    order_uuid = serializers.UUIDField(required=True)
    wallet_pay = serializers.BooleanField(required=True)
