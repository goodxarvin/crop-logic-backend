from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BasePrice, PriceHistory

@receiver(post_save, sender=BasePrice)
def log_price_change(sender, instance, created, **kwargs):
    if created:
        PriceHistory.objects.create(
            sku=instance.sku,
            price_type="BASE",
            old_price=0,
            new_price=instance.amount,
            currency=instance.currency
        )
    else:
        original = BasePrice.objects.get(pk=instance.pk)
        if original.amount != instance.amount:
            PriceHistory.objects.create(
                sku=instance.sku,
                price_type="BASE",
                old_price=original.amount,
                new_price=instance.amount,
                currency=instance.currency
            )