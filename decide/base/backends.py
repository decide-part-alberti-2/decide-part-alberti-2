from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from base import mods
import secrets

from django.core.mail import send_mail
from django.conf import settings

UserModel = get_user_model()

class AuthBackend(ModelBackend):
    '''
    This class makes the login to the authentication method for the django
    admin web interface.

    If the content-type is x-www-form-urlencoded, a requests is done to the
    authentication method to get the user token and this token is stored
    for future admin queries.
    '''

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Verifica si username es un correo electrónico
        if '@' in username:
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None
        else:
            # Si username no es un correo electrónico, usa el nombre de usuario
            user = super().authenticate(request, username=username, password=password, **kwargs)

        # Verifica la contraseña si se encontró un usuario
        if user and user.check_password(password):
            return user
        else:
            return None
    