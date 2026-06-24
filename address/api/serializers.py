from rest_framework import serializers
from ..models import Address, City, Province


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ["province_id", "province_name"]


class CitySerializer(serializers.ModelSerializer):
    province_id = serializers.CharField(source="province.province_id")

    class Meta:
        model = City
        fields = ["city_local_id", "city_name", "province_id"]


class AddressSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(
        source="province.province_name", read_only=True
    )
    city_name = serializers.CharField(source="city.city_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    absolute_url = serializers.SerializerMethodField(
        method_name="get_absolute_url", read_only=True
    )
    relative_url = serializers.URLField(source="get_absolute_relative_url")

    class Meta:
        model = Address
        fields = [
            "address_type",
            "receiver_name",
            "latitute",
            "longtitute",
            "receiver_phone",
            "province",
            "province_name",
            "city",
            "city_name",
            "postal_code",
            "address_detail",
            "relative_url",
            "absolute_url",
            "user_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user_email",
            "absolute_url",
            "province_name",
            "city_name",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get("request")
        if not request.parser_context.get("kwargs"):
            rep.pop("province_name")
            rep.pop("city_name")
            rep.pop("created_at")
            rep.pop("updated_at")

        else:
            rep.pop("absolute_url")
            rep.pop("relative_url")

        return rep

    def get_absolute_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.pk)
