from rest_framework.viewsets import ReadOnlyModelViewSet
from .permissions import IsSuperUser
from .paginations import LedgerPagination
from .serializers import (
    LedgerAccountSerializer,
    LedgerTransactionSerializer,
    LedgerLineSerializer,
)
from ..models import LedgerAccount, LedgerTransaction, LedgerLine


class LedgerAccountViewSet(ReadOnlyModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    pagination_class = LedgerPagination
    serializer_class = LedgerAccountSerializer
    queryset = LedgerAccount.objects.all()


class LedgerTransactionViewSet(ReadOnlyModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    pagination_class = LedgerPagination
    serializer_class = LedgerTransactionSerializer
    queryset = LedgerTransaction.objects.all()


class LedgerLineViewSet(ReadOnlyModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    pagination_class = LedgerPagination
    serializer_class = LedgerLineSerializer
    queryset = LedgerLine.objects.all()
