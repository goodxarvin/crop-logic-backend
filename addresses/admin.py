from django.contrib import admin
from .models import Address, Province, City


class ProvinceAdmin(admin.ModelAdmin):
    model = Province
    list_display = (
        "province_name",
        "province_id",
    )

admin.site.register(Province, ProvinceAdmin)

class CityAdmin(admin.ModelAdmin):
    model = City
    list_display = (
        "city_name",
        "city_local_id",
        "province"
    )

admin.site.register(City, CityAdmin)

class AddressAdmin(admin.ModelAdmin):
    model = Address
    list_display = [
        "address_detail",
        "province",
        "city",
    ]

admin.site.register(Address, AddressAdmin)