from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from ...models import ProductVariant, ProductAttributeValue
from ..serializers import ProductVariantSerializer, ProductAttributeValueSerializer
from ..permissions import IsSuperUser 
from ..paginations import ProductVariantPagination, ProductAttributeValuePaginnation


class ProductVariantViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = ProductVariantSerializer
    pagination_class = ProductVariantPagination
    # queryset = ProductVariant.objects.filter(is_active=True)
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "item__title",
        "name",
        "metadata",
    ]
    filterset_fields = [
        "item",
        "name",
        "is_active",
    ]
    ordering_fields = [
        "created_at",
        "name",
        "updated_at",
    ]

    def get_queryset(self):
        sellable_item_id = self.kwargs["sellable_item_pk"]
        return ProductVariant.objects.filter(Q(is_active=True) & Q(item_id=sellable_item_id))

    def perform_create(self, serializer):
        sellable_item_id = self.kwargs["sellable_item_pk"]
        serializer.save(item_id=sellable_item_id)

class ProductAttributeValueViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = ProductAttributeValueSerializer
    pagination_class = ProductAttributeValuePaginnation
    queryset = ProductAttributeValue.objects.filter(is_active=True)
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "variant__name",
        "value",
        "price_delta",
        "metadata",
    ]
    filterset_fields = [
        "is_default",
        "price_delta",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "price_delta",
        "display_order",
    ]

    def get_queryset(self):
        variant_id = self.kwargs["variant_pk"]
        return ProductAttributeValue.objects.filter(Q(is_active=True) & Q(variant_id=variant_id))

    def perform_create(self, serializer):
        variant_id = self.kwargs["variant_pk"]
        serializer.save(variant_id=variant_id)