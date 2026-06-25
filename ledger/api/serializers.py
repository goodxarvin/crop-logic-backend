from rest_framework import serializers
from ..models import LedgerAccount, LedgerTransaction, LedgerLine


class LedgerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerAccount
        fields = [
            "uuid",
            "name",
            "account_type",
            "code",
            "created_at",
            "updated_at",
        ]


class LedgerTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerTransaction
        fields = [
            "uuid",
            "description",
            "wallet_transaction",
            "created_at",
        ]


class LedgerLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerLine
        fields = [
            "uuid",
            "ledger_transaction",
            "account",
            "amount",
            "created_at",
        ]
