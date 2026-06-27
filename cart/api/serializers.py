from rest_framework import serializers
from pricing.services import PricingService
from ..models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem
        fields = [
            "uuid",
            "cart",
            "sku",
            "quantity",
            "farm",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "cart",
            "created_at",
            "updated_at",
        ]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "quantity must be equal or more than one."
            )
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(
        source="cart_items",
        many=True,
        read_only=True,
    )
    total_items = serializers.IntegerField(
        source="total_items_count",
        read_only=True,
    )
    total_base_price = serializers.FloatField(
        source="total_items_base_price",
        read_only=True,
    )
    total_discount = serializers.FloatField(
        source="total_items_discount_price",
        read_only=True,
    )
    total_price = serializers.FloatField(
        source="total_items_price",
        read_only=True,
    )

    class Meta:
        model = Cart
        fields = [
            "uuid",
            "user",
            "items",
            "total_items",
            "total_base_price",
            "total_discount",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
