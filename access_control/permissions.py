from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.permissions import BasePermission

from farm_hub.models import FarmHub

from .services import is_feature_enabled_for_farm


class FeatureAccessPermission(BasePermission):
    message = "You do not have access to this API."

    def has_permission(self, request, view):
        feature_code = getattr(view, "required_feature_code", None)
        if not feature_code:
            return True

        farm_uuid = self._extract_farm_uuid(request, view)
        if not farm_uuid:
            return True

        farm = self._resolve_owned_farm(request, farm_uuid)
        if farm is None:
            return True

        if is_feature_enabled_for_farm(farm, feature_code):
            return True

        self.message = f"Access to feature `{feature_code}` is denied."
        return False

    @staticmethod
    def _extract_farm_uuid(request, view):
        for key in ("farm_uuid", "farmUuid"):
            farm_uuid = view.kwargs.get(key)
            if farm_uuid:
                return str(farm_uuid)

        for key in ("farm_uuid", "farmUuid"):
            farm_uuid = request.query_params.get(key)
            if farm_uuid:
                return farm_uuid

        if isinstance(request.data, dict):
            for key in ("farm_uuid", "farmUuid"):
                farm_uuid = request.data.get(key)
                if farm_uuid:
                    return farm_uuid
        return None

    @staticmethod
    def _resolve_owned_farm(request, farm_uuid):
        try:
            return (
                FarmHub.objects.select_related("access_profile")
                .prefetch_related("products", "sensors")
                .filter(farm_uuid=farm_uuid, owner=request.user)
                .first()
            )
        except (ValueError, TypeError, DjangoValidationError):
            return None
