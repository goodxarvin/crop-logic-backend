from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from ..paginations import WalletPagination, TransactionPagination
from ..permissions import IsSuperUser
from ..serializers import WalletSerializer, TransactionSerializer
from ...models import Wallet, Transaction


# get access for superusers to wallet model
class WalletListViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = WalletSerializer
    pagination_class = WalletPagination
    queryset = Wallet.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    search_fields = [
        "uuid",
        "user__email",
        "user__first_name",
        "user__last_name",
        "balance",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "available_balance",
        "held_balance",
        "pending_settlements",
        "last_activity",
    ]
    filterset_fields = [
        "currency",
        "status",
    ]


# get access for superusers to transaction model
class TransactionListViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    queryset = Transaction.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    search_fields = [
        "uuid",
        "wallet__uuid",
        "reference_id",
        "title",
        "description",
        "operator_note",
        "metadata",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "amount",
    ]
    filterset_fields = [
        "transaction_type",
        "direction_type",
        "status_type",
        "method",
    ]
