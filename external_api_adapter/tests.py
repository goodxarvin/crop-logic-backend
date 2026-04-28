import uuid
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .adapter import ExternalAPIAdapter


class ExternalAPIAdapterTests(SimpleTestCase):
    @override_settings(EXTERNAL_API_TIMEOUT=30)
    @patch("external_api_adapter.adapter.requests.request")
    def test_request_serializes_uuid_payload_for_json_requests(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"ok": True}
        farm_uuid = uuid.uuid4()

        adapter = ExternalAPIAdapter(
            service_registry=type(
                "Registry",
                (),
                {"get": lambda self, name: {"base_url": "https://example.com", "api_key": "token"}},
            )()
        )

        adapter.request(
            "ai",
            "/api/farm-alerts/tracker/",
            method="POST",
            payload={"farm_uuid": farm_uuid},
        )

        mock_request.assert_called_once()
        request_kwargs = mock_request.call_args.kwargs
        self.assertEqual(request_kwargs["json"], {"farm_uuid": str(farm_uuid)})

    @override_settings(EXTERNAL_API_TIMEOUT=30)
    @patch("external_api_adapter.adapter.requests.request")
    def test_request_serializes_uuid_payload_for_multipart_requests(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {"ok": True}
        farm_uuid = uuid.uuid4()

        adapter = ExternalAPIAdapter(
            service_registry=type(
                "Registry",
                (),
                {"get": lambda self, name: {"base_url": "https://example.com", "api_key": "token"}},
            )()
        )

        adapter.request(
            "ai",
            "/api/upload/",
            method="POST",
            payload={"farm_uuid": farm_uuid, "__files__": {"image": ("leaf.jpg", b"data", "image/jpeg")}},
        )

        mock_request.assert_called_once()
        request_kwargs = mock_request.call_args.kwargs
        self.assertEqual(request_kwargs["data"], {"farm_uuid": str(farm_uuid)})
