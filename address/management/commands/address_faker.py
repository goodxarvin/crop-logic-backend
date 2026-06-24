from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth import get_user_model
from random import choice, randint
from django.db.models import Q
from ...models import Address, Province, City

user = get_user_model()

class Command(BaseCommand):
    help = "fake address creator"
    
    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.faker = Faker()

    def handle(self, *args, **options):

        print("creating fake users...")

        user1 = user.objects.create_user(
            phone_number=self.faker.phone_number(),
            email=self.faker.email(),
            username=self.faker.user_name(),
            password="string123",
        )


        user2 = user.objects.create_user(
            phone_number=self.faker.phone_number(),
            email=self.faker.email(),
            username=self.faker.user_name(),
            password="string123",
        )

        print("operation successful...")

        # print(City.objects.values_list("city_local_id", flat=True)[:10])

        print("creating fake addresses")
        for _ in range(10):
            province = Province.objects.get(pk=randint(0, 30))
            city_list = list(City.objects.filter(province=province).values_list(
                "city_local_id", 
                flat=True,))
            city = City.objects.get(Q(province=province) & Q(city_local_id=choice(city_list)))
            address = Address.objects.create(
                for_sensor=choice([True, False]),
                user=user1,
                province=province,
                city=city,
                postal_code=self.faker.postalcode(),
                address_detail=self.faker.address(),
            )

        for _ in range(5):
            province = Province.objects.get(pk=randint(0, 30))
            city_list = City.objects.filter(province=province).values_list(
                "city_local_id",
                flat=True,
            )
            city = City.objects.get(Q(province=province) & Q(city_local_id=choice(city_list)))
            address = Address.objects.create(
                user=user2,
                province=province,
                city=city,
                postal_code=self.faker.postalcode(),
                address_detail=self.faker.address(),
            )

        print("operation successful...")

        self.stdout.write(
            self.style.SUCCESS("fake addresses and accounts created successfully...")
        )
            

