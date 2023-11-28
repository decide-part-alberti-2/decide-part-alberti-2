from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED
)
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
import re
from django.template.loader import get_template
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.views import View
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator

class GetUserView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        return Response(UserSerializer(tk.user, many=False).data)


class LogoutView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        try:
            tk = Token.objects.get(key=key)
            tk.delete()
        except ObjectDoesNotExist:
            pass

        return Response({})

def account_activation_token(user):
    return default_token_generator.make_token(user)

class RegisterView(CreateView):
    template_name = "register.html"
    form_class = UserCreationForm  # Usamos el formulario de creación de usuario predeterminado
    success_url = '/login-view/'  # URL a la que redirigir después de un registro exitoso
    model = User

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.save()

        # Envío de correo electrónico de verificación
        current_site = get_current_site(self.request)
        mail_subject = 'Activa tu cuenta'
        
        # Generar el token de activación
        uid = urlsafe_base64_encode(force_bytes(self.object.pk))
        token = account_activation_token(self.object)

        # Comprobar si se genera correctamente el token
        if not token:
            return HttpResponse('Error al generar el token de activación.')

        # Construir el mensaje del correo electrónico
        message = render_to_string('account_activation_email.html', {
            'user': self.object,
            'domain': current_site.domain,
            'uid': uid,
            'token': token,
        })
        to_email = form.cleaned_data.get('email')

        # Comprobar si se construye correctamente el mensaje
        if not message:
            return HttpResponse('Error al construir el mensaje de correo electrónico.')

        # Enviar el correo electrónico (verifica los valores pasados)
        try:
            send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [to_email],
                fail_silently=False,
            )
            return HttpResponse('Correo electrónico enviado con éxito.')
        except Exception as e:
            # Si hay un error al enviar el correo electrónico, muestra el mensaje de error
            return HttpResponse(f'Error al enviar el correo electrónico: {str(e)}')

    def form_invalid(self, form):
        return HttpResponse("Error en el registro. Por favor, verifica los datos proporcionados.", status=HTTP_400_BAD_REQUEST)

User = get_user_model()

class AccountActivationView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, 'Tu cuenta ha sido activada. Ahora puedes iniciar sesión.')
            return redirect('login-view')  # Redirige a la página de inicio de sesión después de activar la cuenta
        else:
            messages.error(request, 'El enlace de activación es inválido o ha caducado.')
            return redirect('login-view')  # Redirige a la página de inicio de sesión si hay un problema con la activación

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'password1',
            'password2',
            'email',
            'first_name',
            'last_name'
        )
        labels = {
            'username': 'Nombre de usuario',
            'password1': 'Contraseña',
            'password2': 'Repetir contraseña',
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido'
        }

    def clean_username(self, username):
        username = username.lower()
        new = User.objects.filter(username=username)
        if new.exists():
            return True
        if len(username) > 150:
            return True

        username_val_regex = re.search("[^\w@.\-_+]", username)
        if username_val_regex is not None:
            return True
        return False

    def clean_email(self, email):
        email = email.lower()
        new = User.objects.filter(email=email)
        if new.exists():
            return True
        return False

    def clean_password2(self, password1, password2):
        if password1 and password2 and password1 != password2:
            return True
        return False


class LoginView(CreateView):
    template_name = "login.html"
    form_class = CustomUserCreationForm
    model = User

    def post(self, request):
        values = request.POST
        username = values['username']
        pass1 = values['password1']

        user = authenticate(request, username=username, password=pass1)
        if user is not None:
            login(request, user)
            print("Autenticado correctamente")
        else:
            print("Usuario no autenticado")
            return HttpResponse("El nombre de usuario y la contraseña no coinciden", status=HTTP_400_BAD_REQUEST)

        return redirect("/")

    def get(self, request, *args, **kwargs):
        
        return super().get(request, *args, **kwargs)
