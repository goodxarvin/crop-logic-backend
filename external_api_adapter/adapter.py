from dataclasses import dataclass, field
import logging

import requests
from django.conf import settings

from .exceptions import ExternalAPIRequestError
from .exceptions import MockDirectoryNotFound, MockFileNotFound
from .mock_loader import MockLoader
from .services import ServiceRegistry


logger = logging.getLogger(__name__)


@dataclass
class AdapterResponse:
    status_code: int
    data: object
    headers: dict = field(default_factory=dict)
    is_mock: bool = False


class ExternalAPIAdapter:
    def __init__(self, service_registry=None, mock_loader=None):
        self.service_registry = service_registry or ServiceRegistry()
        self.mock_loader = mock_loader or MockLoader()

    def request(self, service_name, path, method="GET", payload=None, query=None, headers=None):
        request_method = method.upper()
        self._validate_method(request_method)
        service = self.service_registry.get(service_name)
        logger.warning(
            "External API adapter request start: service=%s method=%s path=%s payload_type=%s payload_keys=%s query_keys=%s header_keys=%s",
            service_name,
            request_method,
            path,
            type(payload).__name__,
            sorted(payload.keys()) if isinstance(payload, dict) else None,
            sorted(query.keys()) if isinstance(query, dict) else None,
            sorted(headers.keys()) if isinstance(headers, dict) else None,
        )

        use_mock = getattr(settings, "USE_EXTERNAL_API_MOCK", False) and service_name != "ai"
        if use_mock:
            try:
                mock_response = self.mock_loader.load(service_name=service_name, path=path, method=request_method)
                return AdapterResponse(
                    status_code=mock_response.status_code,
                    data=mock_response.data,
                    headers={"X-Mock-File": mock_response.file_path},
                    is_mock=True,
                )
            except (MockDirectoryNotFound, MockFileNotFound):
                pass

        return self._call_real_api(
            service=service,
            path=path,
            method=request_method,
            payload=payload,
            query=query,
            headers=headers,
        )

    def _call_real_api(self, service, path, method, payload=None, query=None, headers=None):
        base_url = service.get("base_url", "").rstrip("/")
        api_key = service.get("api_key", "")
        host_header = service.get("host_header", "").strip()
        if not base_url:
            raise ExternalAPIRequestError("External service base_url is not configured.")
        url = f"{base_url}/{str(path).lstrip('/')}"

        files = None
        request_payload = payload
        request_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if host_header:
            request_headers["Host"] = host_header
        if headers:
            request_headers.update(headers)

        if isinstance(payload, dict) and payload.get("__files__"):
            files = payload["__files__"]
            request_payload = {
                key: value
                for key, value in payload.items()
                if key != "__files__"
            }
            request_headers.pop("Content-Type", None)

        try:
            request_kwargs = {
                "method": method,
                "url": url,
                "params": query,
                "headers": request_headers,
                "timeout": getattr(settings, "EXTERNAL_API_TIMEOUT", 30),
            }
            if files:
                request_kwargs["data"] = request_payload
                request_kwargs["files"] = files
            else:
                request_kwargs["json"] = request_payload

            logger.warning(
                "External API adapter outbound request: method=%s url=%s has_files=%s json_keys=%s data_keys=%s timeout=%s",
                method,
                url,
                bool(files),
                sorted(request_payload.keys()) if isinstance(request_payload, dict) and not files else None,
                sorted(request_payload.keys()) if isinstance(request_payload, dict) and files else None,
                request_kwargs["timeout"],
            )

            response = requests.request(
                **request_kwargs,
            )
        except requests.RequestException as exc:
            raise ExternalAPIRequestError(f"External API request failed for '{url}': {exc}") from exc

        try:
            response_data = response.json()
        except ValueError:
            response_data = response.text

        logger.warning(
            "External API adapter inbound response: method=%s url=%s status_code=%s response_type=%s response_keys=%s text_length=%s",
            method,
            url,
            response.status_code,
            type(response_data).__name__,
            sorted(response_data.keys()) if isinstance(response_data, dict) else None,
            len(response_data) if isinstance(response_data, str) else None,
        )
        logger.warning("Response : %s",response_data)

        return AdapterResponse(
            status_code=response.status_code,
            data=response_data,
            headers=dict(response.headers),
            is_mock=False,
        )

    @staticmethod
    def _validate_method(method):
        supported_methods = {"GET", "POST", "PUT", "DELETE"}
        if method not in supported_methods:
            raise ValueError(f"Unsupported HTTP method '{method}'. Supported methods: {sorted(supported_methods)}")


_default_adapter = ExternalAPIAdapter()


def request(service_name, path, method="GET", payload=None, query=None, headers=None):
    return _default_adapter.request(
        service_name=service_name,
        path=path,
        method=method,
        payload=payload,
        query=query,
        headers=headers,
    )
