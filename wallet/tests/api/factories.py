import factory
from factory.fuzzy import FuzzyChoice
from django.contrib.auth import get_user_model
from pricing.models import Currency
from ...models import (
    Wallet,
    WalletStatus,
    Transaction,
    TransactionType,
    DirectionType,
    StatusType,
    WithdrawalStatus,
    WithdrawalRequest,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = "test_wallet"
    email = "test@test.test"
    phone_number = "123456789"
    password = "qazwsx123890"


class CurrencyFactory:
    class Meta:
        model = Currency

    code = "IRR_test"
    symbol = "rial_test"
    is_base = True
    is_active = True


class WalletFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wallet

    user = factory.SubFactory(UserFactory)
    currency = factory.SubFactory(CurrencyFactory)
    status = WalletStatus.PENDING
    available_balance = 0


class TransactionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Transaction

    wallet = factory.SubFactory(WalletFactory)
    # authority = "test_authority"
    transaction_type = FuzzyChoice(TransactionType.values)
    direction_type = FuzzyChoice(DirectionType.values)
    status_type = FuzzyChoice(StatusType.values)
    amount = 10_000_000.00
