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
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from .serializers import UserSerializer


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


class RegisterView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        if not tk.user.is_superuser:
            return Response({}, status=HTTP_401_UNAUTHORIZED)

        username = request.data.get('username', '')
        pwd = request.data.get('password', '')
        if not username or not pwd:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User(username=username)
            user.set_password(pwd)
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
        except IntegrityError:
            return Response({}, status=HTTP_400_BAD_REQUEST)
        return Response({'user_pk': user.pk, 'token': token.key}, HTTP_201_CREATED)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')

        if not username or not password:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        user = User.objects.filter(username=username).first()

        if user is None or not user.check_password(password):
            return Response({}, status=HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({}, status=HTTP_401_UNAUTHORIZED)

        # Generar un token para la verificación por correo electrónico
        verification_token = secrets.token_urlsafe(20)
        user.verification_token = verification_token
        user.save()

        # Enviar correo electrónico al usuario para la verificación
        verification_link = f'http://127.0.0.1:8000/verify-token/{verification_token}/'  # URL de verificación
        subject = 'Verificación de inicio de sesión'
        message = f'Por favor, haga clic en el siguiente enlace para verificar su inicio de sesión: {verification_link}'
        recipients = [user.email]  # Asegúrate de tener un campo de email en tu modelo de usuario

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipients
        )

        return Response({'message': 'Se ha enviado un enlace de verificación al correo electrónico registrado.'}, HTTP_200_OK)
