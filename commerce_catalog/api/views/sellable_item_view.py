from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from ...models import SellableItem
from ..paginations import SellableItemPagination
from ..permissions import IsSuperUser
from ..serializers import (
    SellableItemAdminSerializer,
    SellableItemListSerializer,
    sellableItemDetailSerializer,
)


class SellableItemAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = SellableItemAdminSerializer
    queryset = SellableItem.objects.filter(is_active=True)
    pagination_class = SellableItemPagination
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "item_type",
        "title",
        "description",
        "short_description",
        "tax_class__name",
        "external_source",
        "external_id",
        "metadata",
    ]
    filterset_fields = [
        "item_type",
        "is_installable",
        "tax_class__name",
        "requires_shipping_address",
        "requires_farm_address",
        "external_source",
    ]
    ordering_fields = [
        "created_at",
        "title",
        "updated_at",
    ]


class SellableItemViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    # serializer_class = SellableItemListSerializer
    queryset = SellableItem.objects.filter(is_active=True)
    pagination_class = SellableItemPagination
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == "retrieve":
            return queryset.prefetch_related(
                "skus",
                "variants__attribute_values",
                "addon_assignments__add_on",
                "skus__bundle_items__bundle",
            )
        elif self.action == "list":
            return queryset.prefetch_related("skus")

        return queryset

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "retrieve":
            return sellableItemDetailSerializer
        return SellableItemListSerializer

    search_fields = [
        "item_type",
        "title",
        "description",
        "short_description",
        "tax_class__name",
        "external_source",
        "external_id",
        "metadata",
    ]
    filterset_fields = [
        "item_type",
        "is_installable",
        "tax_class__name",
        "requires_shipping_address",
        "requires_farm_address",
        "external_source",
    ]
    ordering_fields = [
        "created_at",
        "title",
        "updated_at",
    ]
