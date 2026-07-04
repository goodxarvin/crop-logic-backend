from django.contrib import admin

from .models.sellable_items import SellableItem


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


admin.site.register(SellableItem, SellableItemAdmin)
