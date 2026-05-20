from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..serializers import AddOnAssignmentSerializer, ProductAddOnSerializer
from ..paginations import ProductAddOnPagination, AddOnAssignmentPagination
from ..permissions import IsSuperUser
from ...models import ProductAddOn, AddOnAssignment


class ProductAddOnViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = ProductAddOnSerializer
    pagination_class = ProductAddOnPagination
    queryset = ProductAddOn.objects.filter(is_active=True)
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "name",
        "description",
        "price",
        "metadata",
    ]
    filterset_fields = [
        "is_active",
        "is_multiple",
    ]
    ordering_fields = [
        "price",
        "created_at",
        "updated_at",
    ]

class AddOnAssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = AddOnAssignmentSerializer
    pagination_class = AddOnAssignmentPagination
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
            "add_on__name",
            "sellable_item__title",
    ]

    filterset_fields = [
        "is_required"
    ]

    def get_queryset(self):
        if self.kwargs.get("sellable_item_pk"):
            sellable_item_id = self.kwargs["sellable_item_pk"]
            return AddOnAssignment.objects.filter(sellable_item_id=sellable_item_id)
        elif self.kwargs.get("product_add_on_pk"):
            product_add_on_id = self.kwargs["product_add_on_pk"]
            return AddOnAssignment.objects.filter(add_on_id=product_add_on_id)



    def perform_create(self, serializer):
        if self.kwargs.get("sellable_item_pk"):
            sellable_item_id = self.kwargs["sellable_item_pk"]
            serializer.save(sellable_item_id=sellable_item_id)
            
        elif self.kwargs.get("product_add_on_pk"):
            product_add_on_id = self.kwargs["product_add_on_pk"]
            serializer.save(add_on_id=product_add_on_id)
