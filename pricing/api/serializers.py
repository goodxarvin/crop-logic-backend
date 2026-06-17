from rest_framework import serializers
from ..models import (
    BasePrice,
    PriceTier,
    PriceHistory,
    Currency,
    DiscountPrice,
    DiscountSellableItemRelation,
    DiscountSKURelation,
)


class BasePriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasePrice
        fields = [
            "id",
            "sku",
            "amount",
            "currency",
            "metadata",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")

        if view:
            if "currency_pk" in view.kwargs:
                fields.get("currency").read_only = True

        return fields


class PriceTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceTier
        fields = [
            "id",
            "sku",
            "currency",
            "amount",
            "min_quantity",
            "max_quantity",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")

        if view:
            if "sku_pk" in view.kwargs:
                fields.get("sku").read_only = True

        elif "currency_pk" in view.kwargs:
            fields.get("currency").read_only = True

        return fields


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = [
            "price_type",
            "sku",
            "currency",
            "old_price",
            "new_price",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")

        if view:
            if "sku_pk" in view.kwargs:
                fields.get("sku").read_only = True

        return fields


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            "id",
            "code",
            "symbol",
            "exchange_rate",
            "is_base",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value


class DiscountPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountPrice
        fields = [
            "id",
            "discount_type",
            "amount",
            "percentage",
            "start_date",
            "end_date",
            "usage_limit",
            "used_count",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "used_count",
            "created_at",
            "updated_at",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value


class DiscountSKURelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountSKURelation
        fields = [
            "id",
            "sku",
            "discount",
        ]

        read_only_fields = [
            "id",
        ]

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")

        if view:
            if "sku_pk" in view.kwargs:
                fields.get("sku").read_only = True

            if "discount_pk" in view.kwargs:
                fields.get("discount").read_only = True

        return fields
    
class DiscountSellableItemRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountSellableItemRelation
        fields = [
            "id",
            "sellable_item",
            "discount",
        ]

        read_only_fields = [
            "id",
        ]

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")

        if view:
            if "sellable_item_pk" in view.kwargs:
                fields.get("sellable_item").read_only = True

            if "discount_pk" in view.kwargs:
                fields.get("discount").read_only = True

        return fields