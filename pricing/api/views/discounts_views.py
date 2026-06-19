from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from ..permissions import IsSuperUser
from ..serializers import (
    DiscountPriceSerializer,
    DiscountSellableItemRelationSerializer,
    DiscountSKURelationSerializer,
)
from ..paginations import (
    DiscountPricePagination,
    DiscountSKUSellableItemRelationPagination,
)
from ...models import DiscountPrice, DiscountSellableItemRelation, DiscountSKURelation


class DiscountPriceViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = DiscountPriceSerializer
    queryset = DiscountPrice.objects.filter(is_active=True)
    pagination_class = DiscountPricePagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "amount",
        "percentage",
        "start_date",
        "end_date",
        "metadata",
    ]
    filterset_fields = [
        "is_active",
        "usage_limit",
        "discount_type",
        "start_date",
        "end_date",
    ]
    ordering_fields = [
        "amount",
        "percentage",
        "start_date",
        "usage_limit",
        "end_date",
        "created_at",
        "updated_at",
    ]


class DiscountSKURelationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = DiscountSKURelationSerializer
    pagination_class = DiscountSKUSellableItemRelationPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "sku__title",
        "discount__amount",
        "discount__percentage",
        "discount__start_date",
        "discount__end_date",
        "discount__metadata",
    ]
    filterset_fields = [
        "sku",
        "discount",
    ]
    ordering_fields = [
        "sku__base_price",
        "discount__amount",
        "discount__percentage",
        "discount__start_date",
        "discount__usage_limit",
        "discount__end_date",
        "discount__created_at",
        "discount__updated_at",
    ]

    def get_queryset(self):
        if self.kwargs.get("sku_pk"):
            sku_id = self.kwargs["sku_pk"]
            return DiscountSKURelation.objects.filter(sku_id=sku_id)

        elif self.kwargs.get("discount_pk"):
            discount_id = self.kwargs["discount_pk"]
            return DiscountSKURelation.objects.filter(discount_id=discount_id)

    def perform_create(self, serializer):
        if self.kwargs.get("sku_pk"):
            sku_id = self.kwargs["sku_pk"]
            serializer.save(sku_id=sku_id)

        elif self.kwargs.get("discount_pk"):
            discount_id = self.kwargs["discount_pk"]
            serializer.save(discount_id=discount_id)

class DiscountSellableItemRelationViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = DiscountSellableItemRelationSerializer
    pagination_class = DiscountSKUSellableItemRelationPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "sellable_item__title",
        "sellable_item__description",
        "sellable_item__short_description",
        "sellable_item__metadata",
        "discount__amount",
        "discount__percentage",
        "discount__start_date",
        "discount__end_date",
        "discount__metadata",
    ]
    filterset_fields = [
        "sellable_item",
        "discount",
    ]
    ordering_fields = [
        "sellable_item__base_price",
        "discount__amount",
        "discount__percentage",
        "discount__start_date",
        "discount__usage_limit",
        "discount__end_date",
        "discount__created_at",
        "discount__updated_at",
    ]

    def get_queryset(self):
        if self.kwargs.get("sellable_item_pk"):
            sellable_item_id = self.kwargs["sellable_item_pk"]
            return DiscountSellableItemRelation.objects.filter(sellable_item_id=sellable_item_id)

        elif self.kwargs.get("discount_pk"):
            discount_id = self.kwargs["discount_pk"]
            return DiscountSellableItemRelation.objects.filter(discount_id=discount_id)

    def perform_create(self, serializer):
        if self.kwargs.get("sellable_item_pk"):
            sellable_item_id = self.kwargs["sellable_item_pk"]
            serializer.save(sellable_item_id=sellable_item_id)

        elif self.kwargs.get("discount_pk"):
            discount_id = self.kwargs["discount_pk"]
            serializer.save(discount_id=discount_id)