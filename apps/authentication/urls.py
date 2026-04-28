from django.urls import path
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # login: returns access + refresh JWT tokens after successful authentication
    path("login/", TokenObtainPairView.as_view(), name="auth_login"),

    # refresh: issues a new access token (and rotates refresh token if enabled)
    path("refresh/", TokenRefreshView.as_view(), name="auth_refresh"),

    # verify: checks if a JWT is valid (signature, expiration, structure)
    path("verify/", TokenVerifyView.as_view(), name="auth_verify"),

    # logout: blacklists the refresh token, making it invalid for future use
    path("logout/", TokenBlacklistView.as_view(), name="auth_logout"),
]