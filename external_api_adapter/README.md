# External API Adapter

## Settings

```python
USE_EXTERNAL_API_MOCK = os.getenv("USE_EXTERNAL_API_MOCK", "false").lower() == "true"

EXTERNAL_SERVICES = {
    "ai": {
        "base_url": os.getenv("AI_SERVICE_BASE_URL", ""),
        "api_key": os.getenv("AI_SERVICE_API_KEY", ""),
    },
    "sensor_hub": {
        "base_url": os.getenv("SENSOR_HUB_SERVICE_BASE_URL", ""),
        "api_key": os.getenv("SENSOR_HUB_SERVICE_API_KEY", ""),
    },
}
```

## Usage

```python
from rest_framework.response import Response
from rest_framework.views import APIView

from external_api_adapter import request


class PredictionProxyView(APIView):
    def get(self, request_obj):
        adapter_response = request("ai", "/predict")
        return Response(adapter_response.data, status=adapter_response.status_code)
```
