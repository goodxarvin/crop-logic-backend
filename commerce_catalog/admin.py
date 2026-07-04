from django.contrib import admin

from .models.sellable_items import SellableItem
from .models.skus import SKU


class SellableItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "item_type",
        "is_active",
        "is_installable",
        "requires_shipping_address",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "description",
        "short_description",
        "external_id",
        "external_source",
    )
    list_filter = (
        "item_type",
        "is_active",
        "is_installable",
        "requires_shipping_address",
    )
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}


class SKUAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "item",
        "base_price",
        "is_default",
        "is_active",
        "created_at",
        "updated_at",
    )
    search_fields = ("code", "title", "barcode", "item__title")
    list_filter = ("is_default", "is_active")
    readonly_fields = ("created_at", "updated_at")


admin.site.register(SellableItem, SellableItemAdmin)
admin.site.register(SKU, SKUAdmin)
