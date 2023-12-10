from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login 
from .forms import LoginForm, UserRegistrationForm
from django.core.mail import send_mail
from django.conf import settings

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            usuario_email = cd.get('usuario_email')
            contraseña = cd.get('contraseña')
            print(usuario_email)

            user = None
            if '@' in usuario_email:
                users = User.objects.filter(email=usuario_email)
                if users.exists():
                    user = authenticate(email=usuario_email, password=contraseña)
            else:
                user = authenticate(username=usuario_email, password=contraseña)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Autentificación correcta')
                else:
                    return HttpResponse('Cuenta desactivada')
            else:
                return HttpResponse('Inicio de sesión inválido')
    else:
        form = LoginForm()
        print(user_form.errors)
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

