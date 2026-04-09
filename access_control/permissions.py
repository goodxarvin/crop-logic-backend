from rest_framework.permissions import BasePermission

from farm_hub.models import FarmHub

from .services import AccessControlServiceUnavailable, authorize_feature, get_authorization_action, get_request_data


class FeatureAccessPermission(BasePermission):
    message = "Access denied."

    def has_permission(self, request, view):
        feature_code = getattr(view, "required_feature_code", None)
        if not feature_code:
            return True

        farm_uuid = (
            view.kwargs.get("farm_uuid")
            or request.query_params.get("farm_uuid")
            or get_request_data(request).get("farm_uuid")
        )
        if not farm_uuid:
            self.message = f"Access to feature `{feature_code}` is denied."
            return False

        try:
            farm = FarmHub.objects.select_related("farm_type", "subscription_plan").prefetch_related(
                "products",
                "sensors",
                "sensors__sensor_catalog",
            ).get(farm_uuid=farm_uuid, owner=request.user)
        except FarmHub.DoesNotExist:
            self.message = f"Access to feature `{feature_code}` is denied."
            return False

        try:
            allowed = authorize_feature(farm, request.user, feature_code, get_authorization_action(request.method))
        except AccessControlServiceUnavailable as exc:
            self.message = str(exc)
            return False

        if not allowed:
            self.message = f"Access to feature `{feature_code}` is denied."
        return allowed
