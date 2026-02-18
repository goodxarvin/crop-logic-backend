"""
Account API serializers.
UpdateProfile request/response shapes aligned with frontend types.
"""

from rest_framework import serializers


class UpdateProfileSerializer(serializers.Serializer):
    """
    Request body for PATCH /api/account/profile/ (UpdateProfilePayload).
    """

    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
