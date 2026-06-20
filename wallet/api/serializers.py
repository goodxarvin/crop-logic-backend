from rest_framework import serializers
from ..models import Wallet, Transaction


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

    

    def validate_metadata(self, value):
        if not value:
            return {}
        return value
