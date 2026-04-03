from django.core.management.base import BaseCommand

from farm_hub.catalog import CATALOG_SEED_DATA
from farm_hub.models import FarmType, Product


class Command(BaseCommand):
    help = "Seed farm types and products catalog data."

    def handle(self, *args, **options):
        farm_type_count = 0
        product_count = 0

        for farm_type_name, products in CATALOG_SEED_DATA.items():
            farm_type, created = FarmType.objects.get_or_create(name=farm_type_name)
            farm_type_count += int(created)
            for product_data in products:
                _, product_created = Product.objects.update_or_create(
                    farm_type=farm_type,
                    name=product_data["name"],
                    defaults={key: value for key, value in product_data.items() if key != "name"},
                )
                product_count += int(product_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Farm catalog seeded successfully. Created farm types: {farm_type_count}, products: {product_count}."
            )
        )
