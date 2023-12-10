from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login 
from .forms import LoginForm, UserRegistrationForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

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

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password1'])
            new_user.save()
            print("Usuario guardado exitosamente:", new_user.username)
            
            # Envío del correo electrónico
            subject = 'Confirmar cuenta'
            message = 'Te has registrado correctamente. ¡Gracias por registrarte!'
            from_email = 'tu_email@tu_dominio.com'  # Reemplaza con tu dirección de correo electrónico

            # Envía el correo al correo electrónico proporcionado en el formulario de registro
            to_email = new_user.email
            send_mail(subject, message, settings.EMAIL_HOST_USER, [to_email], fail_silently=False)

            return render(request, 'register_done.html', {'new_user': new_user})
        else:
            print("Errores en el formulario:", user_form.errors)
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'register.html', {'user_form': user_form})

