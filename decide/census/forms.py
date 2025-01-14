from django import forms
from voting.models import Voting

class CensusAddLdapFormVotacion(forms.Form):

    voting = forms.ModelChoiceField(label='Votación a la que desea añadir censo', empty_label="-",
        queryset=Voting.objects.all().filter(end_date__isnull=True),required=True)

    url_ldap = forms.CharField(label='Url del servidor LDAP',
        widget=forms.TextInput(attrs={'placeholder': 'ldap.ServerUrl:Port'}),required=True)

    tree_suffix = forms.CharField(label='Rama del arbol del administrador LDAP',
        widget=forms.TextInput(attrs={'placeholder': 'cn=admin,dc=YourDomain,dc=com'}),required=True)

    branch = forms.CharField(label='Rama a buscar del LDAP',
        widget=forms.TextInput(attrs={'placeholder': 'dc=YourDomain,dc=com'}),required=True)

    pwd = forms.CharField(label='Contraseña del administrador LDAP',
        widget=forms.TextInput(attrs={'placeholder': 'Password'}),required=True)



