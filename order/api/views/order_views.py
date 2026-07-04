from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from ..serializers import OrderSerializer
from ..paginations import OrderPagination
from ...models import Order
from ...services import OrderService


class OrderViewset(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    queryset = Order.objects.all()
    lookup_field = "uuid"

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):

        order = OrderService.create_order(
            user=self.request.user,
            farm=serializer.validated_data.get("farm"),
        )

        serializer.instance = order

    @action(detail=True, methods=["post"], url_path="finilize")
    def finilize(self, request, uuid=None):
        order = self.get_object()

        try:
            finilize_order = OrderService.freeze_and_finilize_order(order)
            serializer = self.get_serializer(finilize_order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
