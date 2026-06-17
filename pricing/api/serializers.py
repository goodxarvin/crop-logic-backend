from rest_framework import serializers
from ..models import BasePrice, PriceTier, PriceHistory, Currency


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
