from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.authentication.views import MeView, PasswordChangeView, RegisterView

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="auth_login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="auth_verify"),
    path("logout/", TokenBlacklistView.as_view(), name="auth_logout"),
    path("register/", RegisterView.as_view(), name="auth_register"),
    path("me/", MeView.as_view(), name="auth_me"),
    path("password-change/", PasswordChangeView.as_view(), name="auth_password_change"),
]