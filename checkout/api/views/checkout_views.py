from rest_framework import viewsets, views, response, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from payment.services import PaymentService
from ..serializers import CheckoutSessionSerializer, InitiateCheckoutSerializer
from ...services import CheckoutService
from ..paginations import SessionPagination
from ...models import CheckoutSession


class CheckoutViewset(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsAdminUser,
    ]
    serializer_class = CheckoutSessionSerializer
    pagination_class = SessionPagination
    lookup_field = "uuid"

    def get_queryset(self):
        return CheckoutSession.objects.filter(user=self.request.user)


class InitiateCheckoutAPIView(views.APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        serializer = InitiateCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_uuid = serializer.validated_data["order_uuid"]
        wallet_pay = serializer.validated_data["wallet_pay"]

        result = CheckoutService.initiate_checkout_payment(
            user=request.user,
            order_uuid=order_uuid,
            wallet_pay=wallet_pay,
        )

        return response.Response(
            result,
            status=status.HTTP_200_OK,
        )


class VerifyCheckoutAPIView(views.APIView):

    def get(self, *args, **kwargs):
        Status = self.request.query_params.get("Status")
        authority = self.request.query_params.get("Authority")

        checkout_session_uuid = self.request.query_params.get("checkout_session_id")
        payment_uuid = self.request.query_params.get("payment_id")
        txn_uuid = self.request.query_params.get("txn_id")
        order_uuid = self.request.query_params.get("order_id")

        if Status == "OK":
            try:
                result = PaymentService.payment_verify_url(
                    checkout_session_uuid=checkout_session_uuid,
                    payment_uuid=payment_uuid,
                    txn_uuid=txn_uuid,
                    order_uuid=order_uuid,
                    authority=authority,
                )
                return response.Response(
                    result,
                    status=status.HTTP_200_OK,
                )

            except Exception as exc:
                return response.Response(
                    {"datails": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return response.Response(
            {"details": "bank did not accept the request"},
            status=status.HTTP_400_BAD_REQUEST,
        )
