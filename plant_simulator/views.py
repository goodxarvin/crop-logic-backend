"""
Plant Simulator API views.
No database. All responses are static mock data.
Response format: {"status": "success"} or {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from config.swagger import status_response
from .mock_data import CONFIG_SLIDERS_ONLY, START_RESPONSE_DATA, STATE_RESPONSE_DATA
from .serializers import success_response, success_with_data


class ConfigView(APIView):
    """
    GET endpoint for simulator configuration (ورود).

    Purpose:
        Returns only sliders (min, max, step, unit, label, default_value, icon).
        Used when loading/entering the simulator page.

    Input parameters:
        None. Query parameters, if sent, are not read or used.

    Response structure:
        - status: string, always "success".
        - data: object with key "sliders" (array of slider configs).

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Plant Simulator"],
        responses={200: status_response("PlantSimulatorConfigResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(success_with_data(CONFIG_SLIDERS_ONLY), status=status.HTTP_200_OK)


class StateView(APIView):
    """
    GET endpoint for plant state, progress, and chart history.

    Purpose:
        Returns static plant state (height, leaves_count, branches_count,
        fruits_count, yield, yield_rate, tick, is_healthy, can_continue),
        progress (growth_progress, light_status, water_status, yield_progress,
        yield_current, yield_rate_current), and chart (labels, height_history,
        leaf_history, yield_history, yield_rate_history). Used during or after
        simulation for UI and chart.

    Input parameters:
        None. Query parameters, if sent, are not read or used.

    Response structure:
        - status: string, always "success".
        - data: object with keys "plant", "progress", "chart" per
          PLANT_SIMULATOR_API.md §3.

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Plant Simulator"],
        responses={200: status_response("PlantSimulatorStateResponse", data=serializers.JSONField())},
    )
    def get(self, request):
        return Response(success_with_data(STATE_RESPONSE_DATA), status=status.HTTP_200_OK)


class StartView(APIView):
    """
    POST endpoint to start simulation.

    Purpose:
        Returns constants, chart config, plant state, progress, and chart
        history. Body may contain environment and growth_speed; not read or used.

    Input parameters:
        - body (optional): JSON. May contain "environment" and "growth_speed".
          Location: body. Not read or validated; not used in response.

    Response structure:
        - status: string, always "success".
        - data: object with "constants", "chart", "plant", "progress", "chart_history".

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorStartResponse", data=serializers.JSONField())},
    )
    def post(self, request):
        return Response(success_with_data(START_RESPONSE_DATA), status=status.HTTP_200_OK)


class StopView(APIView):
    """
    POST endpoint to stop simulation.

    Purpose:
        Accepts stop request. Returns success only. No processing performed.
        Body may be empty or contain session_id; not read or used.

    Input parameters:
        - body (optional): JSON or empty. Location: body. Not read or used.

    Response structure:
        - status: string, always "success".
        No "data" field.

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorStopResponse")},
    )
    def post(self, request):
        return Response(success_response(), status=status.HTTP_200_OK)


class ResetView(APIView):
    """
    POST endpoint to reset simulation.

    Purpose:
        Accepts reset request. Returns success only. No processing performed.
        Body may be empty or contain session_id; not read or used.

    Input parameters:
        - body (optional): JSON or empty. Location: body. Not read or used.

    Response structure:
        - status: string, always "success".
        No "data" field.

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorResetResponse")},
    )
    def post(self, request):
        return Response(success_response(), status=status.HTTP_200_OK)


class EnvironmentView(APIView):
    """
    PATCH endpoint to update environment (slider values).

    Purpose:
        Accepts environment update. Returns success only. No processing
        performed. Body may contain environment and growth_speed; not
        read or used in the response.

    Input parameters:
        - body (optional): JSON. May contain "environment" (object)
          and "growth_speed" (number). Location: body. Not read or used.

    Response structure:
        - status: string, always "success".
        No "data" field.

    No processing or validation is performed on inputs.
    """

    @extend_schema(
        tags=["Plant Simulator"],
        request=OpenApiTypes.OBJECT,
        responses={200: status_response("PlantSimulatorEnvironmentResponse")},
    )
    def patch(self, request):
        return Response(success_response(), status=status.HTTP_200_OK)
