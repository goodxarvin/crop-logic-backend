from __future__ import annotations

from rest_framework.permissions import BasePermission
from farm_hub.models import FarmHub

from .services import (
    AccessControlServiceUnavailable,
    authorize_feature,
    get_authorization_action,
    get_farm_queryset_for_user,
    get_request_data,
    user_is_admin,
)


class AdminAccessPermission(BasePermission):
    message = "Admin access is required."

    def has_permission(self, request, view) -> bool:
        allowed = user_is_admin(request.user)
        if not allowed:
            self.message = "Admin access is required for this route."
        return allowed


class FeatureAccessPermission(BasePermission):
    message = "Access denied."

    def has_permission(self, request, view) -> bool:
        if getattr(view, "admin_only", False) and not user_is_admin(request.user):
            self.message = "Admin access is required for this route."
            return False

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
            farm = get_farm_queryset_for_user(request.user).get(farm_uuid=farm_uuid)
        except FarmHub.DoesNotExist:
            self.message = f"Access to feature `{feature_code}` is denied."
            return False

        try:
            allowed = authorize_feature(
                farm,
                request.user,
                feature_code,
                get_authorization_action(request.method),
                route=request.path,
            )
        except AccessControlServiceUnavailable as exc:
            self.message = str(exc)
            return False

        if not allowed:
            self.message = f"Access to feature `{feature_code}` is denied."
        return allowed
