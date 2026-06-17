from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from ..permissions import IsSuperUser
from ..serializers import (
    BasePriceSerializer,
    PriceTierSerializer,
    PriceHistorySerializer,
)
from ...models import BasePrice, PriceTier, PriceHistory
from ..paginations import (
    BasePricePagination,
    PriceTierPagination,
    PriceHistoryPagination,
)


class BasePriceViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    queryset = BasePrice.objects.all()
    serializer_class = BasePriceSerializer
    pagination_class = BasePricePagination
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "sku__title",
        "sku__description",
        "sku__metadata",
        "amount",
        "currency__code",
        "currency__symbol",
    ]

    filterset_fields = [
        "sku",
        "currency",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "amount",
    ]


class PriceTierViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    # queryset = PriceTier.objects.filter(is_active=True)
    serializer_class = PriceTierSerializer
    pagination_class = PriceTierPagination
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "sku__title",
        "sku__description",
        "sku__metadata",
        "amount",
        "metadata",
        "currency__code",
        "currency__symbol",
    ]

    filterset_fields = [
        "sku",
        "currency",
        "is_active",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "amount",
        "min_quantity",
        "max_quantity",
    ]

    def get_queryset(self):
        sku_id = self.kwargs.get("sku_pk")
        if sku_id:
            return PriceTier.objects.filter(Q(sku_id=sku_id) & Q(is_active=True))
        return PriceTier.objects.filter(is_active=True)

    def perform_create(self, serializer):
        sku_id = self.kwargs.get("sku_pk")
        if sku_id:
            serializer.save(sku_id=sku_id)
        else:
            serializer.save()


class PriceHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = PriceHistorySerializer
    pagination_class = PriceHistoryPagination
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "sku__title",
        "sku__description",
        "sku__metadata",
        "old_price",
        "new_price",
    ]

    filterset_fields = [
        "sku",
        "price_type",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "amount",
    ]

    def get_queryset(self):
        sku_id = self.kwargs.get("sku_pk")
        if sku_id:
            return PriceHistory.objects.filter(sku_id=sku_id)
        return PriceHistory.objects.all()

    def perform_create(self, serializer):
        sku_id = self.kwargs.get("sku_pk")
        if sku_id:
            serializer.save(sku_id=sku_id)
        else:
            serializer.save()
