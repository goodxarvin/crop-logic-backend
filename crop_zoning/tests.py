from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from external_api_adapter.adapter import AdapterResponse
from farm_hub.models import FarmHub, FarmType

from .views import (
    ClusterBlockLiveView,
    ClusterRecommendationsView,
    KOptionsActivateView,
    KOptionsView,
    LocationDataNdviHealthView,
    LocationDataRemoteSensingView,
    LocationDataView,
    RunStatusView,
)


CLUSTER_UUID = "11111111-2222-3333-4444-555555555555"


class LocationDataProxyViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="location-user",
            password="secret123",
            email="location@example.com",
            phone_number="09120000030",
        )
        self.other_user = get_user_model().objects.create_user(
            username="location-other-user",
            password="secret123",
            email="location-other@example.com",
            phone_number="09120000031",
        )
        self.farm_type = FarmType.objects.create(name="Location Farm Type")
        self.farm = FarmHub.objects.create(owner=self.user, farm_type=self.farm_type, name="Farm 1")
        self.other_farm = FarmHub.objects.create(owner=self.other_user, farm_type=self.farm_type, name="Farm 2")

    def _get(self, path):
        request = self.factory.get(path)
        force_authenticate(request, user=self.user)
        return request

    def _post(self, path, data):
        request = self.factory.post(path, data, format="json")
        force_authenticate(request, user=self.user)
        return request

    @patch("crop_zoning.views.external_api_request")
    def test_get_location_data_proxies_query_params_to_ai(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "code": 200,
                "msg": "success",
                "data": {"source": "database", "id": 12, "lon": "51.389000", "lat": "35.689200"},
            },
        )

        response = LocationDataView.as_view()(self._get("/api/location-data/?lat=35.6892&lon=51.389"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["id"], 12)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/location-data/",
            method="GET",
            payload=None,
            query={"lat": "35.6892", "lon": "51.389"},
        )

    def test_post_location_data_rejects_foreign_farm_uuid(self):
        response = LocationDataView.as_view()(
            self._post("/api/location-data/", {"farm_uuid": str(self.other_farm.farm_uuid), "lat": "35.6892", "lon": "51.389"})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"code": 404, "msg": "location پیدا نشد.", "data": None})

    @patch("crop_zoning.views.external_api_request")
    def test_post_ndvi_health_proxies_owned_farm_to_ai(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=200,
            data={
                "code": 200,
                "msg": "success",
                "data": {"ndviIndex": 0.63, "vegetation_health_class": "healthy"},
            },
        )

        response = LocationDataNdviHealthView.as_view()(
            self._post("/api/location-data/ndvi-health/", {"farm_uuid": str(self.farm.farm_uuid)})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["ndviIndex"], 0.63)
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/location-data/ndvi-health/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
            query=None,
        )

    def test_get_remote_sensing_rejects_foreign_farm_uuid(self):
        response = LocationDataRemoteSensingView.as_view()(
            self._get(f"/api/location-data/remote-sensing/?farm_uuid={self.other_farm.farm_uuid}")
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"code": 404, "msg": "مزرعه پیدا نشد.", "data": None})

    @patch("crop_zoning.views.external_api_request")
    def test_post_remote_sensing_passes_through_202_response(self, mock_external_api_request):
        mock_external_api_request.return_value = AdapterResponse(
            status_code=202,
            data={
                "code": 202,
                "msg": "queued",
                "data": {"status": "processing", "task_id": "task-123"},
            },
        )

        response = LocationDataRemoteSensingView.as_view()(
            self._post("/api/location-data/remote-sensing/", {"farm_uuid": str(self.farm.farm_uuid)})
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["data"]["task_id"], "task-123")
        mock_external_api_request.assert_called_once_with(
            "ai",
            "/api/location-data/remote-sensing/",
            method="POST",
            payload={"farm_uuid": str(self.farm.farm_uuid)},
            query=None,
        )

    @patch("crop_zoning.views.external_api_request")
    def test_auxiliary_location_data_endpoints_proxy_to_ai(self, mock_external_api_request):
        mock_external_api_request.side_effect = [
            AdapterResponse(status_code=200, data={"code": 200, "msg": "success", "data": {"status": "success"}}),
            AdapterResponse(status_code=200, data={"code": 200, "msg": "success", "data": {"cluster_count": 2}}),
            AdapterResponse(status_code=200, data={"code": 200, "msg": "success", "data": {"result_id": 5}}),
            AdapterResponse(status_code=200, data={"code": 200, "msg": "success", "data": {"activated_requested_k": 4}}),
            AdapterResponse(status_code=200, data={"code": 200, "msg": "success", "data": {"status": "running"}}),
        ]

        cluster_response = ClusterBlockLiveView.as_view()(
            self._get(f"/api/location-data/remote-sensing/cluster-blocks/{CLUSTER_UUID}/live/"),
            cluster_uuid=CLUSTER_UUID,
        )
        recommendation_response = ClusterRecommendationsView.as_view()(
            self._get(f"/api/location-data/remote-sensing/cluster-recommendations/?farm_uuid={self.farm.farm_uuid}")
        )
        k_options_response = KOptionsView.as_view()(
            self._get("/api/location-data/remote-sensing/results/5/k-options/"),
            result_id=5,
        )
        activate_response = KOptionsActivateView.as_view()(
            self._post("/api/location-data/remote-sensing/results/5/k-options/activate/", {"requested_k": 4}),
            result_id=5,
        )
        run_status_response = RunStatusView.as_view()(
            self._get("/api/location-data/remote-sensing/runs/9/status/"),
            run_id=9,
        )

        self.assertEqual(cluster_response.status_code, 200)
        self.assertEqual(recommendation_response.data["data"]["cluster_count"], 2)
        self.assertEqual(k_options_response.data["data"]["result_id"], 5)
        self.assertEqual(activate_response.data["data"]["activated_requested_k"], 4)
        self.assertEqual(run_status_response.data["data"]["status"], "running")

    def test_new_routes_exist_and_old_crop_zoning_routes_are_removed(self):
        self.assertIs(resolve("/api/location-data/").func.view_class, LocationDataView)
        self.assertIs(resolve("/api/location-data/ndvi-health/").func.view_class, LocationDataNdviHealthView)
        self.assertIs(resolve("/api/location-data/remote-sensing/").func.view_class, LocationDataRemoteSensingView)
        self.assertIs(
            resolve(f"/api/location-data/remote-sensing/cluster-blocks/{CLUSTER_UUID}/live/").func.view_class,
            ClusterBlockLiveView,
        )
        self.assertIs(
            resolve("/api/location-data/remote-sensing/cluster-recommendations/").func.view_class,
            ClusterRecommendationsView,
        )
        self.assertIs(
            resolve("/api/location-data/remote-sensing/results/5/k-options/").func.view_class,
            KOptionsView,
        )
        self.assertIs(
            resolve("/api/location-data/remote-sensing/results/5/k-options/activate/").func.view_class,
            KOptionsActivateView,
        )
        self.assertIs(
            resolve("/api/location-data/remote-sensing/runs/9/status/").func.view_class,
            RunStatusView,
        )

        with self.assertRaises(Resolver404):
            resolve("/api/crop-zoning/area/")
