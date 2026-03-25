from rest_framework import serializers

from drf_spectacular.utils import inline_serializer


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
