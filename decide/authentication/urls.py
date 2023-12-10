from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
 
    path('login/', views.user_login, name='login'),
    path('', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('activate/<int:user_id>/', views.activate_user, name='activate_user'),
    path('activation_success/', views.activation_success, name='activation_success'),
]