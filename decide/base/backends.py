from django.contrib.auth.backends import ModelBackend

from base import mods

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
        u = super().authenticate(request, username=username,
                                 password=password, **kwargs)

        # only doing this for the admin web interface
        if u and request.content_type == 'application/x-www-form-urlencoded':
            data = {
                'username': username,
                'password': password,
            }
            token = mods.post('authentication', entry_point='/login/', json=data)
            request.session['auth-token'] = token['token']

            # Enviar correo electrónico al usuario autenticado
            subject = 'Inicio de sesión exitoso'
            message = 'Se ha iniciado sesión correctamente en la plataforma.'
            recipients = [u.email]  # Asumiendo que el modelo de usuario tiene un campo 'email'

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=recipients
            )

        return u
