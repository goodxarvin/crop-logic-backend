from django.contrib import admin

from .models import SubscriptionPlan


class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "name",
        "code",
        "duration_days",
        "is_active",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "code", "description")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")


admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
