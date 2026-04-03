from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from config.swagger import code_response
from farm_hub.models import FarmHub

from .models import SubscriptionPlan
from .serializers import FarmAccessProfileSerializer, SubscriptionPlanSerializer
from .services import build_farm_access_profile


class AccessControlBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_farm(self, request, farm_uuid):
        try:
            return FarmHub.objects.prefetch_related("products", "sensors", "sensors__sensor_catalog").select_related(
                "farm_type",
                "subscription_plan",
            ).get(
                farm_uuid=farm_uuid,
                owner=request.user,
            )
        except FarmHub.DoesNotExist:
            return None


class SubscriptionPlanListView(AccessControlBaseView):
    @extend_schema(
        tags=["Access Control"],
        responses={200: code_response("SubscriptionPlanListResponse", data=SubscriptionPlanSerializer(many=True))},
    )
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by("name")
        data = SubscriptionPlanSerializer(plans, many=True).data
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)


class FarmAccessProfileView(AccessControlBaseView):
    @extend_schema(
        tags=["Access Control"],
        responses={
            200: code_response("FarmAccessProfileResponse", data=FarmAccessProfileSerializer()),
            404: code_response("FarmAccessProfileNotFoundResponse"),
        },
    )
    def get(self, request, farm_uuid):
        farm = self._get_farm(request, farm_uuid)
        if farm is None:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        data = build_farm_access_profile(farm)
        return Response({"code": 200, "msg": "success", "data": data}, status=status.HTTP_200_OK)

