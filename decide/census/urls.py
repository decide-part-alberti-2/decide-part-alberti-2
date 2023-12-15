from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('addLDAPcensusVotacion/', views.import_census_from_ldap_votacion, name='addLDAPcensusVotacion'),
]
