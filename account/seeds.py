from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q


ADMIN_USER_DATA = {
    "username": "admin",
    "email": "admin@example.com",
    "phone_number": "0912345678",
    "first_name": "admin",
    "last_name": "admin",
    "password": "admin123456",
}


@transaction.atomic
def seed_admin_user():
    user_model = get_user_model()
    lookup = (
        Q(username=ADMIN_USER_DATA["username"])
        | Q(email=ADMIN_USER_DATA["email"])
        | Q(phone_number=ADMIN_USER_DATA["phone_number"])
    )
    matched_users = list(user_model.objects.filter(lookup).order_by("id"))

    if len(matched_users) > 1:
        raise ValueError(
            "Multiple users matched the admin seeder lookup. Resolve duplicates before seeding."
        )

    created = not matched_users
    user = matched_users[0] if matched_users else user_model()
    user.username = ADMIN_USER_DATA["username"]
    user.email = ADMIN_USER_DATA["email"]
    user.phone_number = ADMIN_USER_DATA["phone_number"]
    user.first_name = ADMIN_USER_DATA["first_name"]
    user.last_name = ADMIN_USER_DATA["last_name"]
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(ADMIN_USER_DATA["password"])
    user.save()

    return user, created
