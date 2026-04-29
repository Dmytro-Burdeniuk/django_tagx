# Auth Flow Design

**Date:** 2026-04-29
**Scope:** Registration, /me/ (GET/PATCH), password change — without email verification (requires SMTP, separate stage)

---

## Context

Custom User model is in place (`apps/users/`). JWT infrastructure (simplejwt, blacklist, rotation) is configured. This spec covers the auth flow endpoints that do not require an email service.

---

## Decisions

- **Architecture:** thin views + service layer. Views handle request/response only. Business logic lives in `apps/authentication/services.py`.
- **Register:** activates user immediately (`is_active=True`, `is_email_verified=False`). Returns user + tokens so the client is logged in after registration.
- **Register fields:** email + password only. `first_name`/`last_name` added later via PATCH `/me/`.
- **Serializers:** plain `Serializer` everywhere (no `ModelSerializer`) for explicitness and performance.
- **Email normalization in service:** `email.strip().lower()` before DB operations.
- **Race condition handling:** catch `IntegrityError` from `create_user()` as the authoritative uniqueness check. No pre-check `exists()` query.
- **Exception hierarchy:** `AppError` base in `core/exceptions.py`. Global handler in `core/exception_handler.py` maps domain exceptions to HTTP responses. Services have no DRF dependency.
- **`partial=True`:** used at view instantiation for PATCH, not `required=False` on serializer fields.
- **Password validation:** `django.contrib.auth.password_validation.validate_password` called in both serializer (fast fail) and service (self-contained safety net).
- **`PasswordChangeView`:** POST (common auth API practice).
- **Logout:** `TokenBlacklistView` from simplejwt — client sends refresh token. Standard JWT approach.

---

## File Structure

```
core/
  exceptions.py          ← AppError + domain exceptions
  exception_handler.py   ← maps AppError subclasses to HTTP responses

apps/users/
  serializers.py         ← UserReadSerializer, UserUpdateSerializer

apps/authentication/
  serializers.py         ← RegisterSerializer, PasswordChangeSerializer
  services.py            ← register(), change_password()
  views.py               ← RegisterView, MeView, PasswordChangeView
  urls.py                ← all /api/auth/* endpoints (updated)
```

`config/django/base.py` — `EXCEPTION_HANDLER` added to `REST_FRAMEWORK`.

---

## Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/api/auth/register/` | public | Create account, return user + tokens |
| GET | `/api/auth/me/` | IsAuthenticated | Current user profile |
| PATCH | `/api/auth/me/` | IsAuthenticated | Update first_name / last_name |
| POST | `/api/auth/password-change/` | IsAuthenticated | Change password |

---

## Components

### `core/exceptions.py`

```python
class AppError(Exception):
    default_message = "Application error."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class InvalidCredentialsError(AppError):
    default_message = "Invalid credentials."


class EmailAlreadyExistsError(AppError):
    default_message = "Email already registered."


class WeakPasswordError(AppError):
    default_message = "Password is too weak."
```

---

### `core/exception_handler.py`

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, WeakPasswordError

_EXCEPTION_MAP = {
    InvalidCredentialsError: status.HTTP_400_BAD_REQUEST,
    EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
    WeakPasswordError: status.HTTP_400_BAD_REQUEST,
}


def custom_exception_handler(exc, context):
    for exc_class, status_code in _EXCEPTION_MAP.items():
        if isinstance(exc, exc_class):
            return Response({"detail": str(exc)}, status=status_code)

    return exception_handler(exc, context)
```

---

### `apps/users/serializers.py`

```python
from rest_framework import serializers


class UserReadSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, allow_blank=True)
    last_name = serializers.CharField(max_length=150, allow_blank=True)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=list(validated_data.keys()))
        return instance
```

---

### `apps/authentication/serializers.py`

```python
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
```

---

### `apps/authentication/services.py`

```python
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, WeakPasswordError


def register(email: str, password: str) -> tuple[User, dict[str, str]]:
    email = email.strip().lower()

    try:
        user = User.objects.create_user(email=email, password=password)
    except IntegrityError:
        raise EmailAlreadyExistsError

    return user, _generate_tokens(user)


def change_password(user: User, old_password: str, new_password: str) -> None:
    if not user.check_password(old_password):
        raise InvalidCredentialsError

    try:
        validate_password(new_password, user)
    except DjangoValidationError as e:
        raise WeakPasswordError(", ".join(e.messages))

    user.set_password(new_password)
    user.save(update_fields=["password"])


def _generate_tokens(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
```

---

### `apps/authentication/views.py`

```python
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication import services
from apps.authentication.serializers import PasswordChangeSerializer, RegisterSerializer
from apps.users.serializers import UserReadSerializer, UserUpdateSerializer


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tokens = services.register(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        return Response(
            {"user": UserReadSerializer(user).data, "tokens": tokens},
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        return Response(UserReadSerializer(request.user).data)

    def patch(self, request: Request) -> Response:
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserReadSerializer(serializer.instance).data)


class PasswordChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
```

---

### `apps/authentication/urls.py`

```python
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
```

---

## Settings change

`config/django/base.py`:
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "core.exception_handler.custom_exception_handler",
}
```

---

## Out of Scope

- Email verification (`is_email_verified` flow) — requires SMTP
- Password reset (forgot password) — requires SMTP
- Email change — requires re-verification