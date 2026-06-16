from django.db import models
from django.core.exceptions import ValidationError


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    symbol = models.CharField(max_length=10)
    exchange_rate = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=1.000000,
    )
    is_base = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        
        if self.code:
            self.code = self.code.upper()      
        if self.exchange_rate <= 0:
            raise ValidationError("exchange rate must be more than 0")         
        if self.is_base and self.exchange_rate != 1:
            raise ValidationError("exchange rate of base currency must be 1")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_base:
            Currency.objects.filter(is_base=True).exclude(pk=self.pk).update(is_base=False)
            self.exchange_rate = 1.000000
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.code}: {self.symbol}"

