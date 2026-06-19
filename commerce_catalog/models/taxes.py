from django.db import models


class TaxClass(models.Model):
    name = models.CharField(max_length=51)
    code = models.CharField(max_length=150, unique=True)
    rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.code}"