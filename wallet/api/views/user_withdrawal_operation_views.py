from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from ..serializers import WithdrawalRequestSerializer
from ..paginations import WithdrawalPagination
from ...models import WithdrawalRequest
from ...services import WalletService


class UserWithdrawalRequestAPIView(ListCreateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = WithdrawalRequestSerializer
    pagination_class = WithdrawalPagination

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(
            wallet__user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        user = self.request.user
        wallet = user.wallet

        try:
            WalletService.create_withdrawal_request(
                wallet=wallet,
                amount=serializer.validated_data["amount"],
                shiba_number=serializer.validated_data["shiba_number"],
                account_holder_name=serializer.validated_data["account_holder_name"],
                card_number=serializer.validated_data.get("card_number"),
            )

        except DjangoValidationError as e:
            raise DRFValidationError({"detail": e.message})
