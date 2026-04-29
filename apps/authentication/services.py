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