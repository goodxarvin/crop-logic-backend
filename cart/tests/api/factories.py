import factory
from commerce_catalog.tests.api.factories import BasePriceFactory
from wallet.tests.api.factories import UserFactory
from farm_hub.models import FarmHub, FarmType
from ...models import Cart, CartItem


class CartFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cart

    user = factory.SubFactory(UserFactory)


class FarmTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FarmType

    name = factory.Sequence(lambda n: f"test_farm_type_{n}")


class FarmHubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FarmHub

    owner = factory.SubFactory(UserFactory)
    farm_type = factory.SubFactory(FarmTypeFactory)
    name = factory.Sequence(lambda n: f"test_farm_{n}")
    is_active = True


class CartItemFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = CartItem

        exclude = ("temporary_price",)

    cart = factory.SubFactory(CartFactory)
    temporary_price = factory.SubFactory(BasePriceFactory)
    sku = factory.LazyAttribute(lambda obj: obj.temporary_price.sku)
    farm = factory.SubFactory(FarmHubFactory)
