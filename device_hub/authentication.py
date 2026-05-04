from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class SensorExternalAPIKeyAuthentication(BaseAuthentication):
    keyword = "Api-Key"

    def authenticate(self, request):
        provided_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        expected_key = getattr(settings, "SENSOR_EXTERNAL_API_KEY", "12345")
        if not provided_key:
            raise AuthenticationFailed("API key is required.")
        if provided_key.startswith(f"{self.keyword} "):
            provided_key = provided_key[len(self.keyword) + 1 :]
        if provided_key != expected_key:
            raise AuthenticationFailed("Invalid API key.")
        return (None, None)
