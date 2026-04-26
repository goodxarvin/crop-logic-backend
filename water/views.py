"""
WATER API views.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from config.swagger import farm_uuid_query_param, sensor_uuid_query_param, status_response
from external_api_adapter import request as external_api_request
from farm_hub.models import FarmHub
from .models import WeatherForecastLog
from .serializers import FarmWeatherCardSerializer, WaterNeedPredictionSerializer, WaterStressIndexSerializer, WaterSummarySerializer
from .services import get_water_need_prediction_data, get_water_stress_index_data, get_water_summary_data


class FarmWeatherCardView(APIView):
    """
    GET endpoint for the farm weather card dashboard data.

    Purpose:
        Returns current weather conditions and an intraday temperature chart
        for a given farm. Data is fetched from the AI external adapter.
        If farm_uuid is provided and the farm exists, the result is persisted
        in WeatherForecastLog for historical reference.

    Input parameters:
        - farm_uuid (query, optional): UUID of the farm.

    Response structure:
        - status: string, always "success".
        - data: object matching the farmWeatherCard shape — condition,
          temperature, unit, humidity, windSpeed, windUnit, chartData.
    """

    @extend_schema(
        tags=["WATER"],
        parameters=[
            farm_uuid_query_param(required=False, description="UUID of the farm to fetch weather data for."),
        ],
        responses={200: status_response("FarmWeatherCardResponse", data=FarmWeatherCardSerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        query = {"farm_uuid": str(farm_uuid)} if farm_uuid else {}

        adapter_response = external_api_request(
            "ai",
            "/weather-forecast/card",
            method="GET",
            query=query,
        )

        response_data = adapter_response.data if isinstance(adapter_response.data, dict) else {}
        card_data = response_data.get("result", response_data.get("data", response_data))

        self._persist_log(farm_uuid, card_data)

        return Response(
            {"status": "success", "data": card_data},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _persist_log(farm_uuid, card_data):
        farm = None
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                pass

        WeatherForecastLog.objects.create(
            farm=farm,
            condition=card_data.get("condition", ""),
            temperature=card_data.get("temperature"),
            unit=card_data.get("unit", "°C"),
            humidity=card_data.get("humidity"),
            wind_speed=card_data.get("windSpeed"),
            wind_unit=card_data.get("windUnit", "km/h"),
            chart_data=card_data.get("chartData", {}),
        )


class WeatherFarmBaseView(APIView):
    @staticmethod
    def _get_farm(request, farm_uuid):
        if not farm_uuid:
            return None, Response(
                {"code": 400, "msg": "error", "data": {"farm_uuid": ["This field is required."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid, owner=request.user), None
        except FarmHub.DoesNotExist:
            return None, Response(
                {"code": 404, "msg": "error", "data": {"farm_uuid": ["Farm not found."]}},
                status=status.HTTP_404_NOT_FOUND,
            )

    @staticmethod
    def _extract_result(adapter_data):
        if not isinstance(adapter_data, dict):
            return {}

        data = adapter_data.get("data")
        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            return data["result"]
        if isinstance(data, dict):
            return data

        result = adapter_data.get("result")
        if isinstance(result, dict):
            return result

        return adapter_data

    @staticmethod
    def _error_response(adapter_response):
        response_data = (
            adapter_response.data
            if isinstance(adapter_response.data, dict)
            else {"message": str(adapter_response.data)}
        )
        return Response(
            {"code": adapter_response.status_code, "msg": "error", "data": response_data},
            status=adapter_response.status_code,
        )

    @classmethod
    def _fetch_water_need_prediction_data(cls, farm_uuid):
        adapter_response = external_api_request(
            "ai",
            "/api/weather/water-need-prediction/",
            method="POST",
            payload={"farm_uuid": str(farm_uuid)},
        )
        if adapter_response.status_code >= 400:
            return None, cls._error_response(adapter_response)

        prediction_data = cls._extract_result(adapter_response.data)
        if isinstance(prediction_data, dict):
            prediction_data.setdefault("farm_uuid", str(farm_uuid))
        return prediction_data, None


class WeatherFarmCardView(WeatherFarmBaseView):
    @extend_schema(
        tags=["WEATHER"],
        request=serializers.Serializer,
        responses={200: status_response("WeatherFarmCardResponse", data=FarmWeatherCardSerializer())},
    )
    def post(self, request):
        farm, error_response = self._get_farm(request, request.data.get("farm_uuid"))
        if error_response is not None:
            return error_response

        adapter_response = external_api_request(
            "ai",
            "/api/weather/farm-card/",
            method="POST",
            payload={"farm_uuid": str(farm.farm_uuid)},
        )
        if adapter_response.status_code >= 400:
            return self._error_response(adapter_response)

        card_data = self._extract_result(adapter_response.data)
        FarmWeatherCardView._persist_log(farm.farm_uuid, card_data)
        return Response({"code": 200, "msg": "success", "data": card_data}, status=status.HTTP_200_OK)


class WaterNeedPredictionView(APIView):
    @extend_schema(
        tags=["WATER"],
        parameters=[
            farm_uuid_query_param(required=False, description="UUID of the farm to fetch water need prediction for."),
        ],
        responses={200: status_response("WaterNeedPredictionResponse", data=WaterNeedPredictionSerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                farm = None
            else:
                prediction_data, error_response = WeatherFarmBaseView._fetch_water_need_prediction_data(farm.farm_uuid)
                if error_response is not None:
                    return error_response
                return Response(
                    {"status": "success", "data": prediction_data},
                    status=status.HTTP_200_OK,
                )
        else:
            farm = None

        return Response(
            {"status": "success", "data": get_water_need_prediction_data(farm)},
            status=status.HTTP_200_OK,
        )


class WaterStressIndexView(APIView):
    @staticmethod
    def _get_farm(farm_uuid):
        if not farm_uuid:
            raise serializers.ValidationError({"farm_uuid": ["This field is required."]})
        try:
            return FarmHub.objects.get(farm_uuid=farm_uuid)
        except FarmHub.DoesNotExist as exc:
            raise serializers.ValidationError({"farm_uuid": ["Farm not found."]}) from exc

    @staticmethod
    def extract_stress_payload(adapter_data, farm_uuid):
        if not isinstance(adapter_data, dict):
            return {
                "farm_uuid": str(farm_uuid),
                "waterStressIndex": 0,
                "level": "",
                "sourceMetric": {},
            }

        data = adapter_data.get("data") if isinstance(adapter_data.get("data"), dict) else adapter_data
        result = data.get("result") if isinstance(data, dict) and isinstance(data.get("result"), dict) else data

        return {
            "farm_uuid": str(farm_uuid),
            "waterStressIndex": int(result.get("waterStressIndex") or 0),
            "level": str(result.get("level") or ""),
            "sourceMetric": result.get("sourceMetric") if isinstance(result.get("sourceMetric"), dict) else {},
        }

    @extend_schema(
        tags=["WATER"],
        parameters=[
            farm_uuid_query_param(required=True, description="UUID of the farm to fetch water stress index for."),
            sensor_uuid_query_param(),
        ],
        responses={200: status_response("WaterStressIndexResponse", data=WaterStressIndexSerializer())},
    )
    def get(self, request):
        farm_uuid = request.query_params.get("farm_uuid")
        sensor_uuid = request.query_params.get("sensor_uuid")
        farm = self._get_farm(farm_uuid)

        query = {"farm_uuid": str(farm.farm_uuid)}
        if sensor_uuid:
            query["sensor_uuid"] = str(sensor_uuid)

        adapter_response = external_api_request(
            "ai",
            "/api/water/stress-index/",
            method="GET",
            query=query,
        )

        if adapter_response.status_code >= 400:
            return Response(
                {
                    "code": adapter_response.status_code,
                    "msg": "error",
                    "data": adapter_response.data if isinstance(adapter_response.data, dict) else {"message": str(adapter_response.data)},
                },
                status=adapter_response.status_code,
            )

        stress_payload = self.extract_stress_payload(adapter_response.data, farm.farm_uuid)

        return Response(
            {"code": 200, "msg": "success", "data": stress_payload},
            status=status.HTTP_200_OK,
        )


class WaterSummaryView(APIView):
    @extend_schema(
        tags=["WATER"],
        parameters=[
            farm_uuid_query_param(required=False, description="UUID of the farm to fetch water summary for."),
        ],
        responses={200: status_response("WaterSummaryResponse", data=WaterSummarySerializer())},
    )
    def get(self, request):
        farm = None
        farm_uuid = request.query_params.get("farm_uuid")
        if farm_uuid:
            try:
                farm = FarmHub.objects.get(farm_uuid=farm_uuid)
            except (FarmHub.DoesNotExist, Exception):
                farm = None

        return Response(
            {"status": "success", "data": get_water_summary_data(farm)},
            status=status.HTTP_200_OK,
        )
