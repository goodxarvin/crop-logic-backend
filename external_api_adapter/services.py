from django.conf import settings

from .exceptions import ServiceNotFound


class ServiceRegistry:
    def __init__(self):
        self._services = getattr(settings, "EXTERNAL_SERVICES", {})

    def get(self, service_name):
        service = self._services.get(service_name)
        if service is None:
            raise ServiceNotFound(f"Unknown external service: '{service_name}'")
        return service
