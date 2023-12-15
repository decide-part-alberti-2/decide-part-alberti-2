from django.urls import path
from . import views
from .views import GetUserView, LogoutView

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('authentication/login/', views.user_login, name='login'),
    path('login-form/', views.login_form, name='login-form'),
    path('authentication/logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', views.register, name='register'),
    path('activate/<int:user_id>/', views.activate_user, name='activate_user'),
    path('activation_success/', views.activation_success, name='activation_success'),
]