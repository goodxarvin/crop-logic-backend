import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from rest_framework.permissions import IsAuthenticated
from ...services import WalletService
from ...models import Wallet, Transaction, StatusType


class WalletTopupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        amount = request.data.get("amount")
        wallet = user.wallets

        txn = WalletService.create_topup_transaction(
            wallet=wallet,
            method="zarinpal",
            amount=amount if amount else Decimal("0"),
        )

        zarinpal_request_url = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"

        payload = {
            "merchant_id": "00000000-0000-0000-0000-000000000000",
            "amount": int(txn.amount) if int(txn.amount) >= 1000 else 1000,
            "description": f"Topup of {txn.amount} {wallet.currency.code} for user {user.email}",
            "callback_url": f"http://localhost:8000/api/wallet/wallets/topup/callback/?txn_id={txn.uuid}",
            "metadata": {
                "mobile": user.phone_number,
                "email": user.email,
            },
        }

        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            response = requests.post(
                zarinpal_request_url, json=payload, headers=headers, timeout=10
            )
            response_data = response.json()

            if response_data.get("data") and response_data["data"].get("code") in [
                100,
                101,
            ]:
                official_authority = response_data["data"]["authority"]
                payment_link = (
                    f"https://sandbox.zarinpal.com/pg/StartPay/{official_authority}"
                )
                txn.authority = official_authority
                txn.metadata["payment_link"] = payment_link
                txn.save()

                return Response(
                    {
                        "mesaage": "transaction created successfully guide the user to complete the payment",
                        "payment_link": payment_link,
                        "transaction_uuid": str(txn.uuid),
                    },
                    status=status.HTTP_201_CREATED,
                )

            else:
                errors = response_data.get("errors", "unknown error")
                return Response(
                    {
                        "error": "zarinpal payment have failed",
                        "details": errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "error": f"could not connect to zarinpal: {str(e)}",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class WalletTopupCallbackAPIView(APIView):

    def get(self, request):
        bank_authority = request.query_params.get("Authority")
        bank_status = request.query_params.get("Status")
        txn_uudi = request.query_params.get("txn_id")

        if not bank_authority or not txn_uudi:
            return Response(
                {
                    "faulty query params from the bank",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            txn = Transaction.objects.get(uuid=txn_uudi, authority=bank_authority)
        except Transaction.DoesNotExist:
            return Response(
                {
                    "error": "could not find the txn",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if bank_status != "OK":
            txn.status_type = StatusType.REJECTED
            txn.metadata["bank error"] = (
                "user canceled the transaction or payment failed"
            )
            txn.save()
            return Response(
                {
                    "message": "unfinished or unsuccessful payment",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        verify_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"

        payload = {
            "merchant_id": "00000000-0000-0000-0000-000000000000",
            "amount": int(txn.amount) if int(txn.amount) >= 1000 else 1000,
            "authority": bank_authority,
        }

        try:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            response = requests.post(
                verify_url, json=payload, headers=headers, timeout=10
            )
            response_data = response.json()

            if response_data.get("data") and response_data["data"].get("code") in [
                100,
                101,
            ]:
                ref_id = response_data["data"]["ref_id"]

                WalletService.verify_confirm_topup(
                    transaction_uuid=txn.uuid,
                    gateway_ref_id=str(ref_id),
                )

                return Response(
                    {
                        "message": "successful payment, wallet charged.",
                        "ref_id": ref_id,
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                txn.status_type = StatusType.REJECTED
                txn.metadata["verify_error"] = response_data.get("errors")
                txn.save()
                return Response(
                    {"error": "bank did not accept the transaction"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"error while connecting to bank servers: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
