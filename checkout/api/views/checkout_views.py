from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from ..serializers import CheckoutSessionSerializer
from ..paginations import SessionPagination
from ...models import CheckoutSession
from ...services import CheckoutService


class CheckoutViewset(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CheckoutSessionSerializer
    pagination_class = SessionPagination
    queryset = CheckoutSession.objects.all()
    lookup_field = "uuid"

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):

        # cart = Cart.objects.filter(user=self.request.user).first()
        checkout_session = CheckoutService.create_checkout_session(
            user=self.request.user,
            farm=serializer.validated_data.get("farm"),
        )

        serializer.instance = checkout_session

    @action(detail=True, methods=["post"], url_path="finilize")
    def finilize(self, request, uuid=None):
        checkout_session = self.get_object()

        try:
            finilize_checkout = CheckoutService.freeze_and_finilize_session(
                checkout_session
            )
            serializer = self.get_serializer(finilize_checkout)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
