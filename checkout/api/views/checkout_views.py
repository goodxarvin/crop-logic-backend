from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..serializers import CheckoutSessionSerializer
from ..paginations import SessionPagination
from ...models import CheckoutSession


class CheckoutViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CheckoutSessionSerializer
    pagination_class = SessionPagination
    lookup_field = "uuid"

    def get_queryset(self):
        return CheckoutSession.objects.filter(user=self.request.user)
