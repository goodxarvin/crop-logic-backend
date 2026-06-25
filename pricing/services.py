from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from .models import (
    DiscountType,
    DiscountSKURelation,
    DiscountSellableItemRelation,
    BasePrice,
    PriceTier,
)


class PricingService:

    @classmethod
    def get_sku_price_unit(cls, sku, quantity: int) -> tuple:
        price_tier = (
            PriceTier.objects.filter(
                sku=sku,
                is_active=True,
                min_quantity__lte=quantity,
            )
            .filter(Q(max_quantity__gte=quantity) | Q(max_quantity__isnull=True))
            .select_related("currency")
            .first()
        )

        if price_tier:
            return (price_tier.currency, price_tier.amount)

        base_price = (
            BasePrice.objects.filter(
                sku=sku,
            )
            .select_related("currency")
            .first()
        )

        if not base_price:
            raise ValueError("there is not tier or base price for this sku.")

        return (base_price.currency, base_price.amount)

    @classmethod
    def get_active_discount(cls, sku):

        now = timezone.now()

        discount_filter = Q(
            discount__is_active=True,
            discount__start_date__lte=now,
            discount__end_date__gte=now,
        ) | Q(
            discount__is_active=True,
            discount__start_date__isnull=True,
            discount__end_date__isnull=True,
        )

        discount_sku_rel = (
            DiscountSKURelation.objects.select_related("discount")
            .filter(
                discount_filter,
                sku=sku,
            )
            .first()
        )

        if discount_sku_rel and (
            discount_sku_rel.discount.usage_limit == 0
            or discount_sku_rel.discount.used_count
            < discount_sku_rel.discount.usage_limit
        ):
            return discount_sku_rel

        sellable_item = getattr(sku, "sellable_item", None)
        discount_sellable_item_rel = (
            DiscountSellableItemRelation.objects.select_related("discount")
            .filter(
                discount_filter,
                sellable_item=sellable_item,
            )
            .first()
        )

        if discount_sellable_item_rel and (
            discount_sellable_item_rel.usage_limit == 0
            or discount_sellable_item_rel.used_count
            < discount_sellable_item_rel.usage_limit
        ):
            return discount_sellable_item_rel

        return None

    @classmethod
    def calculate_final_sku_price(cls, sku, quantity: int, farm=None) -> dict:

        currency, unit_price = cls.get_sku_price_unit(sku=sku, quantity=quantity)
        available_discount = cls.get_active_discount(sku=sku).discount

        discount_amount_per_unit = Decimal("0.00")
        if available_discount:
            if available_discount.discount_type == DiscountType.PERCENTAGE:
                discount_amount_per_unit = unit_price * (
                    Decimal(available_discount.percentage) / Decimal("100")
                )
            elif available_discount.discount_type == DiscountType.FIXED:
                discount_amount_per_unit = available_discount.amount

        final_price_per_unit = max(
            unit_price - discount_amount_per_unit, Decimal("0.00")
        )

        total_base_price = unit_price * quantity
        total_discount_amount = discount_amount_per_unit * quantity
        total_final_price = final_price_per_unit * quantity

        return {
            "currecny_code": currency.code,
            "currency_symbol": currency.symbol,
            "unit_price": float(unit_price),
            "discount_amount_per_unit": float(discount_amount_per_unit),
            "final_price_per_unit": float(final_price_per_unit),
            "total_base_price": float(total_base_price),
            "total_discount_amount": float(total_discount_amount),
            "total_final_price": float(total_final_price),
        }
