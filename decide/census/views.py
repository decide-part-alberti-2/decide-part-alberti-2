from pyexpat.errors import messages
from django.db.utils import IntegrityError
from .forms import CensusAddLdapFormVotacion
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED as ST_201,
        HTTP_204_NO_CONTENT as ST_204,
        HTTP_400_BAD_REQUEST as ST_400,
        HTTP_401_UNAUTHORIZED as ST_401,
        HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from .models import Census
from django.shortcuts import render
from .admin import get_related_object, CensusAdmin
from django.contrib import admin
from .models import LdapCensus
from django.contrib.auth.models import User

class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        voting_id = request.data.get('voting_id')
        voters = request.data.get('voters')
        try:
            for voter in voters:
                census = Census(voting_id=voting_id, voter_id=voter)
                census.save()
        except IntegrityError:
            return Response('Error try to create census', status=ST_409)
        return Response('Census created', status=ST_201)

    def list(self, request, *args, **kwargs):
        voting_id = request.GET.get('voting_id')
        voters = Census.objects.filter(voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})

    def view_census(request):
        censuses = Census.objects.all()
        cs = []

        for census in censuses:
            c = []
            c.append(census.id)
            c.append(getattr(get_related_object('Voting',census.voting_id),get_related_object('Voting',census.voting_id)._meta.fields[1].name))
            c.append(getattr(get_related_object('User',census.voter_id),get_related_object('User',census.voter_id)._meta.fields[4].name))
            cs.append(c)

        return render(request, 'view_census.html', {'cs': cs})

    def import_census_from_csv(request):
        if request.method == 'POST':
            admin_instance = CensusAdmin(Census, admin.site)
            admin_instance.import_from_csv(request, None)
            return render(request, 'import_census.html')

        return render(request, 'import_census_form.html')

class CensusDetail(generics.RetrieveDestroyAPIView):

    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')

def import_census_from_ldap_votacion(request):
    if request.method == 'POST':
        return handle_post_request(request)
    else:
        return handle_get_request(request)

def handle_post_request(request):
    form = CensusAddLdapFormVotacion(request.POST)

    if form.is_valid():
        url_ldap = form.cleaned_data['urlLdap']
        tree_suffix = form.cleaned_data['treeSuffix']
        pwd = form.cleaned_data['pwd']
        branch = form.cleaned_data['branch']
        voting = form.cleaned_data['voting'].__getattribute__('pk')
        username_list = LdapCensus().ldapGroups(url_ldap, tree_suffix, pwd, branch)
        voters = User.objects.all()
        user_list = []

    for username in username_list:
        user = voters.filter(username=username)
        if user:
            user = user.values('id')[0]['id']
            user_list.append(user)

    import_users_to_census(request, voting, user_list)

    return redirect('/admin/census/census')

def import_users_to_census(request, voting, user_list):
    if request.user.is_authenticated:
        for username in user_list:
            census = Census(voting_id=voting, voter_id=username)

            try:
                census.save()
            except IntegrityError:
                messages.add_message(request, messages.ERROR, "Algunos usuarios no se importaron porque ya estaban inscritos en el censo")

def handle_get_request(request):
    form = CensusAddLdapFormVotacion()
    context = {'form': form}

    return render(request, template_name='LDAPvotacion.html', context=context)



