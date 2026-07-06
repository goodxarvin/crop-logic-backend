import factory
from factory.fuzzy import FuzzyChoice
from django.contrib.auth import get_user_model
from pricing.models import Currency
from ledger.models import LedgerAccount, AccountType
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


class TopupTransactionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Transaction

    wallet = factory.SubFactory(WalletFactory)
    authority = "S00000000000000000000000000000n8jggj"
    transaction_type = TransactionType.TOPUP
    direction_type = DirectionType.CREDIT
    status_type = StatusType.PENDING
    amount = 10_000_000.00


class BankLedgerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LedgerAccount

    name = "zarinpal ledger account"
    account_type = AccountType.ASSET
    code = "zarinpal_1001"


class WithdrawalRequestFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = WithdrawalRequest

    wallet = factory.SubFactory(WalletFactory)
    amount = 100_000
    shiba_number = "test_shiba_number"
    account_holder_name = "test_account_holder"
    status = WithdrawalStatus.PENDING
