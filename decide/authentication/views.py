from rest_framework.response import Response
from rest_framework.status import (
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED
)
from django.contrib.auth import authenticate, login
from .forms import LoginForm, UserRegistrationForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from .serializers import UserSerializer
from django.db import IntegrityError
import json

class GetUserView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        return Response(UserSerializer(tk.user, many=False).data)


class LogoutView(APIView):
    def post(self, request):
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                key = data.get('token')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
        else:
            key = request.POST.get('token')
        try:
            tk = Token.objects.get(key=key)
            tk.delete()
        except ObjectDoesNotExist:
            print("El token no existe")

        return Response({})

def user_login(request):
    if request.method == 'POST':
        # Obtiene los datos del cuerpo de la solicitud como JSON
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
        else:
            username = request.POST.get('username')
            password = request.POST.get('password') 
        if username and password:
            user = None
            if '@' in username:
                # Si es un correo electrónico, busca por email
                user = User.objects.filter(email=username).first()
            else:
                # Si no es un correo, busca por nombre de usuario
                user = User.objects.filter(username=username).first()
            if user is not None:
                # Realiza la autenticación del usuario
                auth_user = authenticate(request, username=username, password=password)
                if auth_user is not None:
                    # Obtiene o crea el token si la autenticación es exitosa
                    token, _ = Token.objects.get_or_create(user=auth_user)

                    # Inicia sesión al usuario autenticado
                    login(request, auth_user)

                    # Retorna el token en la respuesta
                    return JsonResponse({'token': token.key, 'message': 'Autenticación exitosa'})
            else:
                return JsonResponse({'message': 'Cuenta desactivada o credenciales inválidas'})

    return JsonResponse({'error': 'Solicitud incorrecta'}, status=400)


def login_form(request):
    return render(request, 'login.html')

def activate_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = True
    user.save()
    return redirect('activation_success')  # Redirige a la página de inicio de sesión después de la activación

def activation_success(request):
    return render(request, 'activation_email.html')

def register(request):
    if request.method == 'POST':
        if request.content_type == 'application/json':
            key = None
            if request.content_type == 'application/json':
                try:
                    data = request.POST if request.POST else json.loads(request.body)
                    key = data.get('token', '')
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
            else:
                key = request.POST.get('token', '')
            try:
                tk = Token.objects.get(key=key)
            except ObjectDoesNotExist:
                return JsonResponse({'error': 'Token inválido'}, status=400)

            if not tk.user.is_superuser:
                return JsonResponse({}, status=401)

            username = data.get('username', '')
            pwd = data.get('password', '')
            if not username or not pwd:
                return JsonResponse({}, status=400)

            try:
                user = User.objects.create_user(username=username, password=pwd)
                token, _ = Token.objects.get_or_create(user=user)
            except IntegrityError:
                return JsonResponse({}, status=400)

            # Envío de correo electrónico para activación
            send_activation_email(user)

            return JsonResponse({'user_pk': user.pk, 'token': token.key}, status=201)
        else:
            user_form = UserRegistrationForm(request.POST or None)
            if user_form.is_valid():
                new_user = user_form.save(commit=False)
                new_user.set_password(user_form.cleaned_data['password'])
                new_user.save()

                # Envío de correo electrónico para activación
                send_activation_email(new_user)

                return render(request, 'register_done.html', {'new_user': new_user})
            else:
                print("Errores en el formulario:", user_form.errors)
    else:
        user_form = UserRegistrationForm()
    return render(request, 'register.html', {'user_form': user_form})

def send_activation_email(user):
    activation_link = f"{settings.BASEURL}{reverse('activate_user', args=[user.id])}"
    message = (
        f"¡Gracias por registrarte! Para activar tu cuenta, haz clic en el siguiente enlace:\n\n"
        f"{activation_link}\n\n"
        f"Si el enlace no funciona, cópialo y pégalo en la barra de direcciones de tu navegador."
    )
    subject = 'Activa tu cuenta'
    from_email = settings.EMAIL_HOST_USER
    to_email = user.email
    send_mail(subject, message, from_email, [to_email])
