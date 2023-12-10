from django.http import HttpResponse
from django.contrib.auth import authenticate, login 
from .forms import LoginForm, UserRegistrationForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            cd = form.cleaned_data
            usuario_email = cd.get('usuario_email')
            password1 = cd.get('password1')
            
            user = None
            if usuario_email and '@' in usuario_email:
                # Si es un correo electrónico, busca por email
                user = User.objects.filter(email=usuario_email).first()
            else:
                # Si no es un correo, busca por nombre de usuario
                user = User.objects.filter(username=usuario_email).first()

            if user is not None:
                user = authenticate(username=user.username, password=password1)
                if user is not None and user.is_active:
                    login(request, user)
                    print("Usuario logueado correctamente")
                    return HttpResponse('Autentificación correcta')
                else:
                    return HttpResponse('Cuenta desactivada o credenciales inválidas')
            else:
                return HttpResponse('Inicio de sesión inválido')
    else:
        form = LoginForm()
        print(form.errors) 
    return render(request, 'login.html', {'form': form})

def activate_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = True
    user.save()
    return redirect('activation_success')  # Redirige a la página de inicio de sesión después de la activación

def activation_success(request):
    return render(request, 'activation_email.html') 

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password1'])
            new_user.save()

            # Obtener el ID del usuario registrado
            user_id = new_user.id

            # Construir el enlace de activación usando la vista de activación y el ID del usuario
            activation_link = f"{settings.BASEURL}{reverse('activate_user', args=[user_id])}"

            # Mensaje del correo electrónico
            message = (
                f"¡Gracias por registrarte! Para activar tu cuenta, haz clic en el siguiente enlace:\n\n"
                f"{activation_link}\n\n"
                f"Si el enlace no funciona, cópialo y pégalo en la barra de direcciones de tu navegador."
            )

            # Enviar el correo electrónico
            subject = 'Activa tu cuenta'
            from_email = settings.EMAIL_HOST_USER
            to_email = new_user.email

            send_mail(subject, message, from_email, [to_email])

            return render(request, 'register_done.html', {'new_user': new_user})
        else:
            print("Errores en el formulario:", user_form.errors)
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'register.html', {'user_form': user_form})
