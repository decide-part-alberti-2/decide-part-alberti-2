from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from .views import GetUserView, LogoutView, RegisterView, LoginView

urlpatterns = [
    path('verify-token/<str:verification_token>/', LoginView.as_view(), name='verificar_inicio_sesion'),
    path('login/', obtain_auth_token),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view()),
]
