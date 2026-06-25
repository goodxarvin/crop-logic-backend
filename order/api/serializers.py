from rest_framework import serializers
from ..models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "uuid",
            "checkout_session_uuid",
            "total_amount",
            "status",
            "shipping_address_snapshot",
            "farm_address_snapshot",
            "items_snapshot",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
