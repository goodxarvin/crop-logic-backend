from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from farm_hub.models import FarmHub

from .services import (
    AccessControlServiceUnavailable,
    authorize_feature,
    get_authorization_action,
    get_request_data,
    get_route_feature_code,
)


class RouteFeatureAccessMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        view_class = getattr(view_func, "view_class", None)
        if view_class is None:
            return None

        if self._allows_anonymous(view_class):
            return None

        user = self._get_authenticated_user(request)
        if user is None:
            return None

        app_label = view_class.__module__.split(".", 1)[0]
        feature_code = get_route_feature_code(app_label)
        if not feature_code:
            return None

        farm_uuid = view_kwargs.get("farm_uuid") or request.GET.get("farm_uuid") or get_request_data(request).get("farm_uuid")
        farm = None
        if farm_uuid:
            try:
                farm = FarmHub.objects.select_related("farm_type", "subscription_plan").prefetch_related(
                    "products",
                    "sensors",
                    "sensors__sensor_catalog",
                ).get(farm_uuid=farm_uuid, owner=user)
            except FarmHub.DoesNotExist:
                return JsonResponse(
                    {"code": 403, "msg": f"Access to route feature `{feature_code}` is denied."},
                    status=403,
                )

        try:
            allowed = authorize_feature(
                farm=farm,
                user=user,
                feature_code=feature_code,
                action=get_authorization_action(request.method),
                route=request.path,
            )
        except AccessControlServiceUnavailable as exc:
            return JsonResponse({"code": 503, "msg": str(exc)}, status=503)

        if not allowed:
            return JsonResponse(
                {"code": 403, "msg": f"Access to route feature `{feature_code}` is denied."},
                status=403,
            )

        request.route_feature_code = feature_code
        return None

    @staticmethod
    def _allows_anonymous(view_class):
        for permission_class in getattr(view_class, "permission_classes", []):
            if permission_class is AllowAny:
                return True
        return False

    @staticmethod
    def _get_authenticated_user(request):
        if getattr(request, "user", None) is not None and request.user.is_authenticated:
            return request.user

        authenticator = JWTAuthentication()
        try:
            auth_result = authenticator.authenticate(request)
        except (InvalidToken, TokenError):
            return None

        if auth_result is None:
            return None

        user, _token = auth_result
        request.user = user
        request._cached_user = user
        return user
