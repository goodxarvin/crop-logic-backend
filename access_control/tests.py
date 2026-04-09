from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from account.views import ProfileView

from .middleware import RouteFeatureAccessMiddleware
from .services import batch_authorize_features, build_authorization_input


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "access-control-tests",
    }
}


@override_settings(CACHES=TEST_CACHES, ACCESS_CONTROL_AUTHZ_CACHE_TIMEOUT=300)
class AccessControlServiceTests(SimpleTestCase):
    def test_batch_authorize_features_uses_cache_for_same_route(self):
        farm = SimpleNamespace(farm_uuid="farm-uuid")
        user = SimpleNamespace(id=7)

        with patch("access_control.services.request_opa_batch_authorization") as mock_request:
            mock_request.return_value = {"decisions": {"farm_dashboard": True}}

            first_result = batch_authorize_features(
                farm=farm,
                user=user,
                features=["farm_dashboard"],
                action="view",
                route="/api/farm-dashboard/",
            )
            second_result = batch_authorize_features(
                farm=farm,
                user=user,
                features=["farm_dashboard"],
                action="view",
                route="/api/farm-dashboard/",
            )

        self.assertEqual(first_result, {"farm_dashboard": True})
        self.assertEqual(second_result, {"farm_dashboard": True})
        self.assertEqual(mock_request.call_count, 1)

    def test_build_authorization_input_includes_route(self):
        user = SimpleNamespace(
            id=3,
            username="tester",
            email="tester@example.com",
            phone_number="09120000000",
            is_staff=False,
            is_superuser=False,
        )

        payload = build_authorization_input(
            farm=None,
            user=user,
            features=["account_management"],
            action="view",
            route="/api/account/profile/",
        )

        self.assertEqual(payload["route"], "/api/account/profile/")
        self.assertEqual(payload["resource"]["sensor_codes"], [])

    def test_batch_authorize_features_supports_nested_opa_feature_payload(self):
        farm = SimpleNamespace(farm_uuid="farm-uuid")
        user = SimpleNamespace(id=9)

        with patch("access_control.services.request_opa_batch_authorization") as mock_request:
            mock_request.return_value = {
                "features": {
                    "feature1": {"allow": True, "allow_rules": [], "deny_rules": []},
                    "feature2": {"allow": False, "allow_rules": [], "deny_rules": []},
                }
            }

            result = batch_authorize_features(
                farm=farm,
                user=user,
                features=["feature1", "feature2", "feature3"],
                action="view",
                route="/api/farm-dashboard/",
            )

        self.assertEqual(
            result,
            {
                "feature1": True,
                "feature2": False,
                "feature3": False,
            },
        )


class RouteFeatureAccessMiddlewareTests(SimpleTestCase):
    def test_middleware_passes_route_feature_and_method_to_service(self):
        factory = RequestFactory()
        request = factory.patch("/api/account/profile/")
        request.user = SimpleNamespace(is_authenticated=True, id=11)

        middleware = RouteFeatureAccessMiddleware(lambda req: None)
        view = ProfileView.as_view()

        with patch("access_control.middleware.authorize_feature", return_value=True) as mock_authorize:
            response = middleware.process_view(request, view, (), {})

        self.assertIsNone(response)
        mock_authorize.assert_called_once_with(
            farm=None,
            user=request.user,
            feature_code="account_management",
            action="edit",
            route="/api/account/profile/",
        )
