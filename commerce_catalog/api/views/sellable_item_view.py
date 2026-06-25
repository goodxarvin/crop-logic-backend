from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from ...models import SellableItem
from ..paginations import SellableItemPagination
from ..permissions import IsSuperUser
from ..serializers import SellableItemSerializer


class SellableItemViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = SellableItemSerializer
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
