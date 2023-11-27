from django.contrib.auth.backends import ModelBackend

from base import mods
import secrets

from django.core.mail import send_mail
from django.conf import settings


class AuthBackend(ModelBackend):
    '''
    This class makes the login to the authentication method for the django
    admin web interface.

    If the content-type is x-www-form-urlencoded, a requests is done to the
    authentication method to get the user token and this token is stored
    for future admin queries.
    '''

    def authenticate(self, request, username=None, password=None, **kwargs):
    # Verifica si request es None antes de acceder a su contenido
        if request is None:
            return None

        user = super().authenticate(request, username=username, password=password, **kwargs)

        # Verifica si request tiene content_type antes de acceder a él
        if user and hasattr(request, 'content_type') and request.content_type == 'application/x-www-form-urlencoded':
            # Resto de tu lógica aquí...
            # Aquí puedes colocar el mensaje que se enviará al usuario registrado
            message = 'Te has registrado correctamente en nuestra plataforma.'

            # Envío de correo electrónico al usuario registrado
            subject = 'Registro Exitoso'
            recipients = [user.email]  # Asumiendo que el modelo de usuario tiene un campo 'email'

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=recipients
            )

        return user