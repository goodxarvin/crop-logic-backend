from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..permissions import IsSuperUser
from ..serializers import TaxClassSerializer
from ..paginations import TaxClassPaginnation
from ...models import TaxClass

class TaxClassViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser
    ]
    serializer_class = TaxClassSerializer
    pagination_class = TaxClassPaginnation
    queryset = TaxClass.objects.filter(is_active=True)
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "name",
        "code",
        "rate",
        "description",
        "metadata",
    ]
    filterset_fields = [
        "rate",
        "is_active",
    ]
    ordering_fields = [
        "name",
        "rate",
        "created_at",
        "updated_at",
    ]