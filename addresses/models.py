from django.db import models


class Province(models.Model):
    province_id = models.IntegerField(primary_key=True)
    province_name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.province_name}"

class City(models.Model):
    province = models.ForeignKey("Province", on_delete=models.CASCADE, related_name="city")
    city_id = models.IntegerField(primary_key=True)
    city_name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.city_name}"




class Address(models.Model):
    province = models.ForeignKey("Province", on_delete=models.CASCADE, related_name="province")
    city = models.ForeignKey("City", on_delete=models.CASCADE, related_name="city")
    address_detail = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.address_detail[:10]}..."
    