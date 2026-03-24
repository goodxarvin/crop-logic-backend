from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class MultiFieldBackend(ModelBackend):
    """
    Authenticate against username, email, or phone_number.
    Used for password-based login where the user can enter any of the three.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(
                Q(username=username) | Q(email=username) | Q(phone_number=username)
            )
            print(user)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            User().set_password(password)
            return None
        print(user.check_password(password) , self.user_can_authenticate(user))
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
