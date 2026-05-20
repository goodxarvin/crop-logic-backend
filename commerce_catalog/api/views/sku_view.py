from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from commerce_catalog.models.skus import SKU
from ..permissions import IsSuperUser
from ..paginations import SKUPagination
from ..serializers import SKUseralizer



class SKUViewset(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = SKUseralizer
    pagination_class = SKUPagination
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "item__title",
        "code",
        "title",
        "barcode",
        "base_price",
        "attributes",
        "metadata",
    ]
    ordering_fields = [
        "base_price",
        "createed_at",
        "updated_at",
    ]
    filterset_fields = [
        "is_default",
        "is_active",
    ]

    def get_queryset(self):
        sellable_item_id = self.kwargs["sellable_item_pk"]
        return SKU.objects.filter(Q(is_active=True) & Q(item_id=sellable_item_id))

    def perform_create(self, serializer):
        sellable_item_id = self.kwargs["sellable_item_pk"]
        serializer.save(item_id=sellable_item_id)