from django.contrib import admin

from cart.models.cart_models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "created_at", "updated_at")
    search_fields = ("user__username", "uuid")
    list_filter = ("created_at", "updated_at")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("uuid", "cart", "sku", "farm", "quantity", "created_at")
    search_fields = ("sku__name", "cart__user__username", "uuid")
    list_filter = ("created_at", "updated_at", "farm")
