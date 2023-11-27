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


class RegisterView(CreateView):
    template_name = "register.html"
    form_class = UserCreationForm  # Usamos el formulario de creación de usuario predeterminado
    success_url = '/'  # URL a la que redirigir después de un registro exitoso
    model = User

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        return HttpResponse("Error en el registro. Por favor, verifica los datos proporcionados.", status=HTTP_400_BAD_REQUEST)


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


class VerifyTokenView(APIView):
    def get(self, request, verification_token):
        try:
            user = User.objects.get(verification_token=verification_token)
            if user:
                user.is_active = True
                user.save()
                return redirect('/') 
        except User.DoesNotExist:
            return HttpResponse("Token inválido o expirado. Por favor, contacta al soporte.")