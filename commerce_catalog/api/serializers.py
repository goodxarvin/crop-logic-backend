from rest_framework import serializers
from pricing.services import PricingService

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


class SellableItemAdminSerializer(serializers.ModelSerializer):

    class Meta:
        model = SellableItem
        fields = [
            "item_type",
            "title",
            "description",
            "short_description",
            "is_active",
            "is_installable",
            "requires_shipping_address",
            "requires_farm_address",
            "tax_class",
            "external_source",
            "external_id",
            "metadata",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value


class SellableItemListSerializer(serializers.ModelSerializer):

    price = serializers.SerializerMethodField()

    class Meta:
        model = SellableItem
        fields = [
            "id",
            "item_type",
            "title",
            "description",
            "short_description",
            "price",
            "is_active",
            "is_installable",
            "requires_shipping_address",
            "requires_farm_address",
            "image",
            "tax_class",
            "external_source",
            "external_id",
            "metadata",
            "price",
        ]

    def get_price(self, obj):
        return PricingService.calculate_final_sku_price(
            obj.skus.filter(is_default=True, is_active=True).first(), 1
        ).get("total_base_price", 0.00)


class sellableItemDetailSerializer(serializers.ModelSerializer):
    variants = serializers.SerializerMethodField()
    skus = serializers.SerializerMethodField()
    addons = serializers.SerializerMethodField()
    bundles = serializers.SerializerMethodField()

    class Meta:
        model = SellableItem
        fields = [
            "id",
            "item_type",
            "title",
            "description",
            "short_description",
            "is_active",
            "is_installable",
            "requires_shipping_address",
            "requires_farm_address",
            "image",
            "tax_class",
            "external_source",
            "external_id",
            "metadata",
            "variants",
            "skus",
            "addons",
            "bundles",
        ]

    def get_variants(self, obj):
        variants = obj.variants.filter(is_active=True)
        return ProductVariantSerializer(variants, many=True).data

    def get_skus(self, obj):
        skus = obj.skus.filter(is_active=True)
        return SKUseralizer(skus, many=True).data

    def get_addons(self, obj):
        addon_assignments = obj.addon_assignments.filter(add_on__is_active=True)
        return ProductAddOnSerializer(addon_assignments, many=True).data

    def get_bundles(self, obj):
        sku_ids = obj.skus.filter(is_active=True).values_list("id", flat=True)
        bundles = ProductBundle.objects.filter(
            sku_items__sku_id__in=sku_ids,
            is_active=True,
        ).distinct()

        return ProductBundleSerializer(bundles, many=True).data


class ProductVariantSerializer(serializers.ModelSerializer):

    values = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "item",
            "name",
            "is_active",
            "values",
            "metadata",
        ]
        read_only_fields = [
            "item",
        ]

    def validate_metadata(self, value):
        if not value:
            return {}
        return value

    def get_values(self, obj):
        values = obj.attribute_values.filter(is_active=True)
        return ProductAttributeValueSerializer(values, many=True).data


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
            "price",
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
