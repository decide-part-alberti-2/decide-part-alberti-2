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
        u = super().authenticate(request, username=username,
                                 password=password, **kwargs)

        # Solo se realiza esto para la interfaz web de administración
        if u and request.content_type == 'application/x-www-form-urlencoded':
            data = {
                'username': username,
                'password': password,
            }
            token = mods.post('authentication', entry_point='/login/', json=data)
            request.session['auth-token'] = token['token']

            # Generar un token único para la verificación por correo electrónico
            verification_token = secrets.token_urlsafe(20)
            request.session['verification-token'] = verification_token

            # Enviar correo electrónico al usuario autenticado con el enlace de verificación
            verification_link = f'http:/verify-token/'
            subject = 'Verificación de inicio de sesión'
            message = f'Por favor, haga clic en el siguiente enlace para verificar su inicio de sesión: {verification_link} con el token {verification_token}'
            recipients = [u.email]  # Asumiendo que el modelo de usuario tiene un campo 'email'

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=recipients
            )


        return u
