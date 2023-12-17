from django.urls import path
from . import views

urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('view_census/', views.CensusCreate.view_census, name='view_census'),
    path('import_census/', views.CensusCreate.import_census_from_csv, name='import_census'),
]
