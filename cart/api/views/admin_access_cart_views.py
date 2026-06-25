from rest_framework import viewsets
from ..permissions import IsSuperUser
from ..paginations import CartPagination
from ..serializers import CartSerializer
from ...models import Cart


class CartViewset(viewsets.ModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    pagination_class = CartPagination
    serializer_class = CartSerializer
    queryset = Cart.objects.all()
