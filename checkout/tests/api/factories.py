import factory
from django.utils import timezone
from payment.models import Payment, PaymentStatus
from cart.tests.api.factories import UserFactory
from ...models import CheckoutSession, StatusType


class CheckoutSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CheckoutSession

    user = factory.SubFactory(UserFactory)
    status = StatusType.AWAITING_PAYMENT
    payment_deadline_at = timezone.now() + timezone.timedelta(minutes=10)


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    user = factory.SubFactory(UserFactory)
    status = PaymentStatus.PENDING
