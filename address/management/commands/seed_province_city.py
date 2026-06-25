from django.core.management.base import BaseCommand  # , CommandError
import json
from pathlib import Path
from ...models import Province, City


class Command(BaseCommand):
    help = "push all provinces and cities to database"

    def handle(self, *args, **options):
        json_file_path = Path("/app/address/provinces_cities.json")

        with open(json_file_path, "r", encoding="utf-8") as json_file:
            all_data = json.load(json_file)

        print("injecting all provinces to the database...")

        for province_data in all_data:
            province = Province.objects.get_or_create(
                province_id=int(province_data.get("provinceId")),
                province_name=str(province_data.get("provinceName")),
            )

        print("task complete :)")

        print("injecting all the cities to the database ")
        for city_data in all_data:
            city = City.objects.get_or_create(
                city_local_id=str(city_data.get("cityId")),
                city_name=str(city_data.get("cityName")),
                province_id=int(city_data.get("provinceId")),
            )

        print("task complete :)")

        self.stdout.write(
            self.style.SUCCESS(r"all the data successfully injected in the database :>")
        )
