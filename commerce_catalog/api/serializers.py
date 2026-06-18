from rest_framework import serializers

from ..models import (
    SellableItem,
    SKU,
    ProductVariant,
    ProductAttributeValue,
    ProductBundle,
    ProductBundleItem,
    ProductAddOn,
    AddOnAssignment,
    TaxClass,
    )

class SellableItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = SellableItem
        fields = [
            "item_type", 
            "title",
            "description",
            "short_description",
            "is_active",
            "is_installable",
            "requires_farm_context",
            "tax_class",
            "external_source",
            "external_id",
            "metadata",
            ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

class ProductVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductVariant
        fields = [
            "item",
            "name",
            "is_active",
            "metadata",
        ]
        read_only_fields = [
            "item",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

class ProductAttributeValueSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductAttributeValue
        fields = [
            "variant",
            "value",
            "display_order",
            "is_default",
            "is_active",
            "price_delta",
            "metadata",
        ]
        read_only_fields = ["variant"]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

class TaxClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaxClass
        fields = [
            "name",
            "code",
            "rate",
            "description",
            "is_active",
            "metadata",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

class SKUseralizer(serializers.ModelSerializer):

    class Meta:
        model = SKU
        fields = [
            "item",
            "code",
            "title",
            "barcode",
            "base_price",
            "is_default",
            "is_active",
            "attributes",
            "metadata",
        ]
        read_only_fields = [
            "item",
        ]

    def validate_attributes(self, value):
        if not value:
            return {}
        return value

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

class ProductAddOnSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductAddOn
        fields = [
            "name",
            "description",
            'price',
            "is_multiple",
            "is_active",
            "metadata",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

class AddOnAssignmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = AddOnAssignment
        fields = [
            "add_on",
            "sellable_item",
            "is_required",
        ]

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")

        if view:
            if "sellable_item_pk" in view.kwargs:
                fields.get("sellable_item").read_only = True

            elif "product_add_on_pk" in view.kwargs:
                fields.get("add_on").read_only = True

        return fields

class ProductBundleSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductBundle
        fields = [
            "name",
            "bundle_price",
            "discount_amount",
            "is_active",
            "metadata",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

class ProductBundleItemSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = ProductBundleItem
        fields = [
            "bundle",
            "sku",
            "quantity",
        ]

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")

        if view:
            if "sku_pk" in view.kwargs:
                fields.get("sku").read_only = True
            elif "bundle_pk" in view.kwargs:
                fields.get("bundle").read_only = True
            
        return fields
