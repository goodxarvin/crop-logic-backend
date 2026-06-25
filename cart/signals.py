from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cart


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_cart(sender, instance, created, **kwargs):
    if created:
        try:
            Cart.objects.create(
                user=instance,
            )
        except Exception as e:
            print(f"error while creating user cart: {str(e)}")
