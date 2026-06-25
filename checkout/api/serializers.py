from rest_framework import serializers
from ..models import CheckoutSession


class CheckoutSessionSerializer(serializers.ModelSerializer):

    requirements = serializers.JSONField(
        source="get_requirements",
        read_only=True,
    )

    class Meta:
        model = CheckoutSession
        fields = [
            "uuid",
            "cart",
            "farm",
            "status",
            "shipping_address",
            "farm_address",
            "billing_address",
            "requirements",
            "pricing_snapshot",
            "shipping_address_snapshot",
            "farm_address_snapshot",
            "billing_address_snapshot",
            "customer_notes",
            "payment_deadline_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "cart",
            "status",
            "requirements",
            "pricing_snapshot",
            "shipping_address_snapshot",
            "farm_address_snapshot",
            "billing_address_snapshot",
            "payment_deadline_at",
            "created_at",
            "updated_at",
        ]
