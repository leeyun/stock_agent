from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import LoginView, LogoutView, MeView, SignupView

app_name = "trender_auth"

urlpatterns = [
    path("login/",   LoginView.as_view(),       name="login"),
    path("logout/",  LogoutView.as_view(),      name="logout"),
    path("signup/",  SignupView.as_view(),      name="signup"),
    path("me/",      MeView.as_view(),           name="me"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("verify/",  TokenVerifyView.as_view(),  name="verify"),
]