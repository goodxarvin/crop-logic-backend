from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# from django.shortcuts import get_object_or_not_found
from ...models import Cart, CartItem
from ..serializers import CartItemSerializer, CartSerializer


class CartItemViewSet(viewsets.ModelViewSet):

    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CartItemSerializer
    lookup_field = "uuid"

    def get_queryset(self):

        return CartItem.objects.filter(cart__user=self.request.user)

    # def get_serializer_class(self, *args, **kwargs):
    #     if self.action in ["create", "update", "destroy"]:
    #         return CartSerializer
    #     return CartItemSerializer

    def _get_user_cart_response(self):
        cart = Cart.objects.get(user=self.request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        return self._get_user_cart_response()

    def create(self, request, *args, **kwargs):
        cart = self.request.user.cart

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku = serializer.validated_data["sku"]
        quantity = serializer.validated_data["quantity"]
        farm = serializer.validated_data.get("farm", None)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, sku=sku, farm=farm, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return self._get_user_cart_response()

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        self.serializer_class = CartSerializer
        return self._get_user_cart_response()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        self.serializer_class = CartSerializer
        return self._get_user_cart_response()

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"detail": "retrieve response not available"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def perform_create(self, serializer):
        serializer.save(cart=self.request.user.cart)
