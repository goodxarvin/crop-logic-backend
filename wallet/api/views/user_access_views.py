from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from ..paginations import WalletPagination, TransactionPagination
from ..serializers import WalletSerializer, TransactionSerializer
from ...models import Wallet, Transaction


class UserWalletRetrieveAPIView(RetrieveAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = WalletSerializer
    pagination_class = WalletPagination

    def get_object(self):
        user = self.request.user
        object = Wallet.objects.get(user=user)
        return object


class UserTransactionViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(wallet__user=user).order_by("-created_at")
        return queryset
