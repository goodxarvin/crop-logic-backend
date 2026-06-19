from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..paginations import ProductBundlePagination, ProductBundleItemPagination
from ..permissions import IsSuperUser
from ..serializers import ProductBundleSerializer, ProductBundleItemSerializer
from ...models import ProductBundle, ProductBundleItem


class ProductBundleViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = ProductBundleSerializer
    pagination_class = ProductBundlePagination
    queryset = ProductBundle.objects.filter(is_active=True)
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "name",
        "bundle_price",
        "discount_amount"
        "metadata",
    ]
    filterset_fields = [
        "is_active",
    ]
    ordering_fields = [
        "bundle_price",
        "discount_amount",
        "created_at",
        "updated_at",
    ]

class ProductBundleItemViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = ProductBundleItemSerializer
    pagination_class = ProductBundleItemPagination
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "sku__title",
        "budnle__name",
        "quantity",
    ]
    filterset_fields = [
        "quantity",
    ]
    ordering_fields = [
        "quantity",
    ]

    def get_queryset(self):
        if self.kwargs.get("sku_pk"):
            sku_id = self.kwargs["sku_pk"]
            return ProductBundleItem.objects.filter(sku_id=sku_id)
        elif self.kwargs.get("bundle_pk"):
            bundle_id = self.kwargs["bundle_pk"]
            return ProductBundleItem.objects.filter(bundle_id=bundle_id)
    
    def perform_create(self, serializer):
        if self.kwargs.get("sku_pk"):
            sku_id = self.kwargs["sku_pk"]
            serializer.save(sku_id=sku_id)
        elif self.kwargs.get("bundle_pk"):
            bundle_id = self.kwargs["bundle_pk"]
            serializer.save(bundle_id=bundle_id)