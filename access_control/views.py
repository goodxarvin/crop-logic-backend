from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema
from farm_hub.models import FarmHub

from config.swagger import code_response

from .serializers import FeatureAuthorizationRequestSerializer
from .services import (
    AccessControlServiceUnavailable,
    get_farm_queryset_for_user,
    get_user_role,
    request_opa_batch_authorization,
    user_is_admin,
)


class FarmFeatureAuthorizationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Access Control"],
        parameters=[
            OpenApiParameter(name="farm_uuid", type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, default="11111111-1111-1111-1111-111111111111"),
        ],
        request=FeatureAuthorizationRequestSerializer,
        responses={200: code_response("FarmFeatureAuthorizationResponse")},
    )
    def post(self, request, farm_uuid):
        serializer = FeatureAuthorizationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            farm = get_farm_queryset_for_user(request.user).get(farm_uuid=farm_uuid)
        except FarmHub.DoesNotExist:
            return Response({"code": 404, "msg": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            opa_result = request_opa_batch_authorization(
                farm=farm,
                user=request.user,
                features=serializer.validated_data["features"],
                action=serializer.validated_data["action"],
                route=request.path,
            )
        except AccessControlServiceUnavailable as exc:
            return Response(
                {"code": 503, "msg": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": {
                    "farm_uuid": str(farm.farm_uuid),
                    "user": {
                        "id": request.user.id,
                        "username": request.user.username,
                        "email": request.user.email,
                        "phone_number": getattr(request.user, "phone_number", ""),
                    },
                    "features": serializer.validated_data["features"],
                    "action": serializer.validated_data["action"],
                    "decision": opa_result,
                },
            },
            status=status.HTTP_200_OK,
        )


class PanelRoutingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Access Control"],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Returns the panel target for the authenticated user.",
            )
        },
    )
    def get(self, request):
        role = get_user_role(request.user)
        panel = "admin" if user_is_admin(request.user) else "user"
        return Response(
            {
                "code": 200,
                "msg": "success",
                "data": {
                    "panel": panel,
                    "role": role,
                    "permissions": [],
                },
            },
            status=status.HTTP_200_OK,
        )
