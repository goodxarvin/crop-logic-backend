import factory
from factory.fuzzy import FuzzyChoice
from cart.tests.api.factories import UserFactory
from ...models import Address, AddressType


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    address_type = FuzzyChoice(AddressType.values)
    user = factory.SubFactory(UserFactory)
    province_id = FuzzyChoice(range(31))
    city_id = 1
    postal_code = "test_code"
    address_detail = "test_address_detail"
