from rest_framework import serializers


class LocationDataQuerySerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=18, decimal_places=12, required=False)
    lon = serializers.DecimalField(max_digits=18, decimal_places=12, required=False)
    farm_uuid = serializers.UUIDField(required=False)


class LocationDataUpsertSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=False)
    lat = serializers.DecimalField(max_digits=18, decimal_places=12, required=False)
    lon = serializers.DecimalField(max_digits=18, decimal_places=12, required=False)
    farm_boundary = serializers.JSONField(required=False)
    block_layout = serializers.JSONField(required=False)


class FarmUUIDRequestSerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True)


class RemoteSensingQuerySerializer(serializers.Serializer):
    farm_uuid = serializers.UUIDField(required=True)
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class ClusterBlockLiveQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    farm_uuid = serializers.UUIDField(required=False)


class KOptionActivateSerializer(serializers.Serializer):
    requested_k = serializers.IntegerField(min_value=1)
