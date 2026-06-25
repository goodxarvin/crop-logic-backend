from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..serializers import OrderSerializer
from ..paginations import OrderPagination
from ...models import Order


class OrderViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = OrderSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
