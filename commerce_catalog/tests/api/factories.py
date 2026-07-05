import factory
from factory.fuzzy import FuzzyChoice
from pricing.models import BasePrice, Currency
from ...models import (
    SellableItem,
    ItemType,
    TaxClass,
    SKU,
    ProductVariant,
    ProductAttributeValue,
    ProductBundle,
    ProductBundleItem,
    ProductAddOn,
    AddOnAssignment,
)


class TaxClassFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaxClass

    name = factory.Sequence(lambda n: f"test item tax {n}")
    code = factory.Sequence(lambda n: f"{1000+n}")
    rate = 0.90000
    description = "test for item tax"
    is_active = True


class SellableItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SellableItem

    item_type = FuzzyChoice(ItemType.values)
    title = f"{str(item_type).lower()} item"
    slug = factory.Sequence(lambda n: f"item-{n}")
    is_active = True
    tax_class = factory.SubFactory(TaxClassFactory)


class SKUFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SKU

    item = factory.SubFactory(SellableItemFactory)
    code = factory.Sequence(lambda n: f"{1000+n}")
    title = factory.Sequence(lambda n: f"sku test {n}")
    barcode = factory.Sequence(lambda n: f"{n}")
    is_active = True
    is_default = True


class CurrencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Currency
        django_get_or_create = ("code",)

    code = "IRR"
    symbol = "rial"
    is_base = True
    is_active = True


class BasePriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BasePrice

    sku = factory.SubFactory(SKUFactory)
    amount = 1000000
    currency = factory.SubFactory(CurrencyFactory)
