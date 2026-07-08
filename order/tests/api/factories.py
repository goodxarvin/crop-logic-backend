import factory
from cart.tests.api.factories import CartFactory, UserFactory, FarmHubFactory
from address.tests.api.factories import AddressFactory
from ...models import Order, StatusType


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    cart = factory.SubFactory(CartFactory)
    status = StatusType.PENDING
    farm = factory.SubFactory(FarmHubFactory)
    shipping_address = factory.SubFactory(AddressFactory)
    farm_address = factory.SubFactory(AddressFactory)
