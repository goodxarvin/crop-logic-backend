from rest_framework import serializers

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer


FARM_UUID_DEFAULT = "11111111-1111-1111-1111-111111111111"


class AuthTokenSerializer(serializers.Serializer):
    token = serializers.CharField()


def code_response(name, data=None, token=False, extra_fields=None):
    fields = {
        "code": serializers.IntegerField(),
        "msg": serializers.CharField(),
    }
    if data is not None:
        fields["data"] = data
    if token:
        fields["token"] = serializers.CharField()
    if extra_fields:
        fields.update(extra_fields)
    return inline_serializer(name=name, fields=fields)


def status_response(name, data=None):
    fields = {
        "status": serializers.CharField(default="success"),
    }
    if data is not None:
        fields["data"] = data
    return inline_serializer(name=name, fields=fields)


def farm_uuid_query_param(required=False, description="UUID of the farm."):
    return OpenApiParameter(
        name="farm_uuid",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        required=required,
        description=description,
        default=FARM_UUID_DEFAULT,
    )


def sensor_uuid_query_param(required=False, description="Optional sensor UUID."):
    return OpenApiParameter(
        name="sensor_uuid",
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.QUERY,
        required=required,
        description=description,
    )
