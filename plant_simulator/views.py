"""
Plant Simulator API views.
Plain Django only; no DRF. No database. All responses are static mock data.
Response format: {"status": "success"} or {"status": "success", "data": <payload>}. HTTP 200 only.
No processing, validation, or use of input parameters in responses.
CSRF exempt so frontend (e.g. localhost:3000) can call POST/PATCH without token.
"""

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .mock_data import CONFIG_SLIDERS_ONLY, START_RESPONSE_DATA, STATE_RESPONSE_DATA
from .serializers import success_response, success_with_data


@method_decorator(csrf_exempt, name="dispatch")
class ConfigView(View):
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

    def get(self, request):
        return JsonResponse(success_with_data(CONFIG_SLIDERS_ONLY), status=200)


@method_decorator(csrf_exempt, name="dispatch")
class StateView(View):
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

    def get(self, request):
        return JsonResponse(success_with_data(STATE_RESPONSE_DATA), status=200)


@method_decorator(csrf_exempt, name="dispatch")
class StartView(View):
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

    def post(self, request):
        return JsonResponse(success_with_data(START_RESPONSE_DATA), status=200)


@method_decorator(csrf_exempt, name="dispatch")
class StopView(View):
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

    def post(self, request):
        return JsonResponse(success_response(), status=200)


@method_decorator(csrf_exempt, name="dispatch")
class ResetView(View):
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

    def post(self, request):
        return JsonResponse(success_response(), status=200)


@method_decorator(csrf_exempt, name="dispatch")
class EnvironmentView(View):
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

    def patch(self, request):
        return JsonResponse(success_response(), status=200)
