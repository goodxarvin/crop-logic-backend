from rest_framework import serializers
from ..models import Order


class OrderSerializer(serializers.ModelSerializer):

    requirements = serializers.JSONField(
        source="get_requirements",
        read_only=True,
    )

    payable_with_wallet = serializers.BooleanField(
        source="is_payable_with_wallet",
        read_only=True,
    )

    class Meta:
        model = Order
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
            "items_snapshot",
            "total_amount",
            "payable_with_wallet",
            "customer_notes",
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
            "items_snapshot",
            "total_amount",
            "payable_with_wallet",
            "created_at",
            "updated_at",
        ]
