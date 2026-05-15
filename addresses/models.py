from django.db import models
from config.settings import AUTH_USER_MODEL
from django.urls import reverse

class Province(models.Model):
    province_id = models.IntegerField(primary_key=True)
    province_name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.province_id}: {self.province_name}"

class City(models.Model):
    province = models.ForeignKey("Province", on_delete=models.CASCADE, related_name="city")
    city_local_id = models.CharField(max_length=3, null=True, blank=True)
    city_name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.city_local_id}: {self.city_name}"




class Address(models.Model):
    for_sensor = models.BooleanField(default=False, null=True)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    province = models.ForeignKey("Province", on_delete=models.CASCADE, related_name="province")
    city = models.ForeignKey("City", on_delete=models.CASCADE, related_name="city")
    postal_code = models.CharField(max_length=15, null=True)
    address_detail = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.address_detail[:10]}..."

    def get_absolute_relative_url(self):
        return reverse("addresses:address-api-urls:address-viewset-detail", kwargs={"pk": self.pk})