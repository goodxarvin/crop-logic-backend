from rest_framework import serializers
from ..models import Wallet, Transaction, WithdrawalRequest


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = [
            "uuid",
            "user",
            "status",
            "currency",
            "available_balance",
            "held_balance",
            "pending_settlements",
            "total_balance",
            "last_activity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "user", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and not request.user.is_staff:
            excluded_fields = [
                "uuid",
                "user",
            ]
            for field_name in excluded_fields:
                self.fields.pop(field_name, None)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "uuid",
            "wallet",
            "transaction_type",
            "direction_type",
            "status_type",
            "amount",
            "reference_id",
            "reference_type",
            "method",
            "balance_after",
            "metadata",
            "title",
            "description",
            "reason_code",
            "operator_note",
            "actor_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "wallet", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and not request.user.is_staff:
            excluded_fields = [
                "uuid",
                "wallet",
                "actor_id",
                "operator_note",
                "metadata",
                "reference_id",
                "method",
            ]
            for field_name in excluded_fields:
                self.fields.pop(field_name, None)

    def validate_metadata(self, value):
        if not value:
            return {}
        return value


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = [
            "uuid",
            "wallet",
            "amount",
            "shiba_number",
            "card_number",
            "account_holder_name",
            "status",
            "transaction",
            "rejection_reason",
            "bank_tracking_code",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "status",
            "rejection_reason",
            "bank_tracking_code",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")

        if request and not request.user.is_staff:
            excluded_fields = [
                "uuid",
                "wallet",
                "transaction",
            ]
            for field_name in excluded_fields:
                self.fields.pop(field_name, None)

    def validate_shiba_number(self, value):
        value = value.strip().upper()
        if not value.startswith("IR") or len(value) != 26:
            raise serializers.ValidationError(
                "shiba needs to start with IR and it must be 26 caracters"
            )
        return value


class WithdrawalActionSerializer(serializers.Serializer):
    bank_tracking_code = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
