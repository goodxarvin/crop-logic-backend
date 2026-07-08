from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ...models import Cart, CartItem
from ..serializers import CartItemSerializer, CartSerializer


class CartItemViewSet(viewsets.GenericViewSet):

    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CartSerializer
    # lookup_field = "uuid"

    def get_object(self):

        return get_object_or_404(Cart, user=self.request.user)

    # def get_serializer_class(self, *args, **kwargs):
    #     if self.action in ["create", "update", "destroy"]:
    #         return CartSerializer
    #     return CartItemSerializer

    def _get_user_cart_response(self, cart, status_code=status.HTTP_200_OK):
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status_code)

    def list(self, request, *args, **kwargs):
        cart = self.get_object()
        return self._get_user_cart_response(cart, status_code=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=CartItemSerializer,
        url_path="add-item",
    )
    def add_item(self, request, *args, **kwargs):
        cart = self.get_object()

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

        return self._get_user_cart_response(
            cart=cart, status_code=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=["post"],
        serializer_class=CartItemSerializer,
        url_path="add-item-quantity",
    )
    def add_one_item_quantity(self, request, *args, **kwargs):
        cart = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku = serializer.validated_data["sku"]
        farm = serializer.validated_data.get("farm", None)

        cart_item = get_object_or_404(CartItem, cart=cart, sku=sku, farm=farm)
        quantity = cart_item.quantity

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity += 1
            cart_item.save(update_fields=["quantity"])

        return self._get_user_cart_response(cart=cart, status_code=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=CartItemSerializer,
        url_path="subtract-item-quantity",
    )
    def subtract_one_item_quantity(self, request, *args, **kwargs):
        cart = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku = serializer.validated_data["sku"]
        farm = serializer.validated_data.get("farm", None)

        cart_item = get_object_or_404(CartItem, cart=cart, sku=sku, farm=farm)
        quantity = cart_item.quantity

        if quantity <= 1:
            cart_item.delete()
        else:
            cart_item.quantity -= 1
            cart_item.save(update_fields=["quantity"])

        return self._get_user_cart_response(cart=cart, status_code=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=CartItemSerializer,
        url_path="remove-item",
    )
    def remove_item(self, request, *args, **kwargs):
        cart = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku = serializer.validated_data["sku"]
        farm = serializer.validated_data.get("farm", None)

        cart_item = get_object_or_404(CartItem, cart=cart, sku=sku, farm=farm)
        cart_item.delete()
        return self._get_user_cart_response(cart=cart, status_code=status.HTTP_200_OK)
