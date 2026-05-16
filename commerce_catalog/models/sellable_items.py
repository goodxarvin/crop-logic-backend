from django.db import models

class SellableItem(models.Model):
    item_type = models.CharField(choices=)