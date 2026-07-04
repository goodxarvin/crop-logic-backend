from django.contrib import admin

from .models.fullfilment_models import InstallationRequest, Shipment, ShipmentItem


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "address",
        "carrier",
        "status",
        "shipped_at",
        "delivered_at",
    )
    list_filter = ("status", "carrier")
    search_fields = ("tracking_number", "order__id", "address__city")


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "shipment",
        "cart_item",
        "quantity",
        "allocated_device_serial_number",
    )
    search_fields = ("shipment__id", "cart_item__id", "allocated_device_serial_number")


@admin.register(InstallationRequest)
class InstallationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cart_item",
        "farm",
        "status",
        "scheduled_for",
        "assigned_team",
    )
    list_filter = ("status",)
    search_fields = ("assigned_team", "cart_item__id", "farm__name")
