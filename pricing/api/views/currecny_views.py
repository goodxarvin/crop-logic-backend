from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..permissions import IsSuperUser
from ..serializers import CurrencySerializer
from ..paginations import CurrencyPagination
from ...models import Currency


class CurrencyViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = CurrencySerializer
    pagination_class = CurrencyPagination
    queryset = Currency.objects.all()
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "code",
        "symbol",
        "exchange_rate",
        "metadata",
    ]
    filterset_fields = [
        "is_base",
        "is_active",
    ]
    ordering_fields = [
        "exchange_rate",
        "created_at",
        "updated_at",
    ]
