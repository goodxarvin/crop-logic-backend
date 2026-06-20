from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from ..permissions import IsSuperUser
from ..serializers import WithdrawalRequestSerializer, WithdrawalActionSerializer
from ..paginations import WithdrawalPagination
from ...services import WalletService
from ...models import WithdrawalRequest, WithdrawalStatus


class AdminPendingViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsSuperUser,
    ]
    serializer_class = WithdrawalRequestSerializer
    pagination_class = WithdrawalPagination
    queryset = WithdrawalRequest.objects.filter(
        status=WithdrawalStatus.PENDING
    ).order_by("created_at")


class AdminWithdrawalProcessAPIView(APIView):
    permission_classes = [
        IsSuperUser,
    ]

    def post(self, request, uuid, action_type):

        serializer = WithdrawalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            if action_type == "approve":
                track_code = serializer.validated_data.get("bank_tracking_code")
                if not track_code:
                    return Response(
                        {"error": "must enter bank_tracking_code"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                req = WalletService.approve_withdrawal_request(
                    request_uuid=uuid, bank_tracking_code=track_code
                )
                return Response(
                    {
                        "message": "withdrawal request submitted successfully",
                        "status": req.status,
                    }
                )

            elif action_type == "reject":
                reason = serializer.validated_data.get("rejection_reason")
                if not reason:
                    return Response(
                        {"error": "must enter the rejection reason"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                req = WalletService.reject_withdrawal_request(
                    request_uuid=uuid, rejection_reason=reason
                )
                return Response(
                    {
                        "message": "withdrawal request rejectd and money transfered to wallet again",
                        "status": req.status,
                    }
                )

            else:
                return Response(
                    {"error": "unapproved action"}, status=status.HTTP_400_BAD_REQUEST
                )

        except DjangoValidationError as e:
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)
