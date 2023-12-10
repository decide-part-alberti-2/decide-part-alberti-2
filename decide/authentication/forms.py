from django import forms
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    usuario_email = forms.CharField()
    contraseña = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        usuario_email = cleaned_data.get('usuario_email')
        contraseña = cleaned_data.get('contraseña')

        if usuario_email and contraseña:
   
            if '@' in usuario_email:
                users = User.objects.filter(email=usuario_email)
                if users.exists():
                    user = authenticate(email=usuario_email, password=contraseña)
                    if user:
                        cleaned_data['user'] = user
                        return cleaned_data
            else:
                user = authenticate(username=usuario_email, password=contraseña)
                if user:
                    cleaned_data['user'] = user
                    return cleaned_data

            raise forms.ValidationError('Credenciales inválidas. Por favor, verifica tu usuario/email y contraseña.')


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña' , widget=forms.PasswordInput )
    password2 = forms.CharField(label='Repite la contraseña' , widget=forms.PasswordInput )


    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'email': 'Correo electrónico',
            'last_name': 'Apellido',
           
        }

    def clean_contraseña2(self):  
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('La contraseña no coincide')
        return cd['password12']