from django.db.models.signals import post_save
from django.conf import settings
from django.dispatch import receiver
from django.db.models import Q
from .models import Wallet
from pricing.models import Currency


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        try:
            IRR_currency, _ = Currency.objects.get_or_create(
                (Q(code="IRR") | Q(symbol="rial")),
                is_base=True,
                is_active=True,
                defaults={
                    "code": "IRR",
                    "symbol": "rial",
                },
            )
            Wallet.objects.create(
                user=instance,
                currency=IRR_currency,
            )
            print("user wallet created successfully")

        except Exception as e:
            print(f"Error creating user wallet: {str(e)}")
