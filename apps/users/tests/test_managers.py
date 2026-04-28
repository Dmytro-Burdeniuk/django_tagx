import pytest

from apps.users.models import User


@pytest.mark.django_db
def test_create_user_stores_correct_email():
    user = User.objects.create_user(email="test@example.com", password="secret123")
    assert user.email == "test@example.com"


@pytest.mark.django_db
def test_create_user_normalizes_email_domain():
    user = User.objects.create_user(email="test@EXAMPLE.COM", password="secret123")
    assert user.email == "test@example.com"


@pytest.mark.django_db
def test_create_user_sets_usable_password():
    user = User.objects.create_user(email="test@example.com", password="secret123")
    assert user.check_password("secret123")


@pytest.mark.django_db
def test_create_user_with_none_password_creates_unusable_password():
    user = User.objects.create_user(email="test@example.com", password=None)
    assert not user.has_usable_password()


def test_create_user_with_empty_email_raises():
    with pytest.raises(ValueError, match="Email is required"):
        User.objects.create_user(email="", password="secret123")


def test_create_user_with_none_email_raises():
    with pytest.raises(ValueError, match="Email is required"):
        User.objects.create_user(email=None, password="secret123")


@pytest.mark.django_db
def test_create_superuser_sets_all_permission_flags():
    user = User.objects.create_superuser(email="admin@example.com", password="secret123")
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True
    assert user.is_email_verified is True


def test_create_superuser_with_none_password_raises():
    with pytest.raises(ValueError, match="Superuser must have a password"):
        User.objects.create_superuser(email="admin@example.com", password=None)


def test_create_superuser_with_empty_password_raises():
    with pytest.raises(ValueError, match="Superuser must have a password"):
        User.objects.create_superuser(email="admin@example.com", password="")


def test_create_superuser_with_is_staff_false_raises():
    with pytest.raises(ValueError, match="Superuser must have is_staff=True"):
        User.objects.create_superuser(
            email="admin@example.com", password="secret123", is_staff=False
        )


def test_create_superuser_with_is_superuser_false_raises():
    with pytest.raises(ValueError, match="Superuser must have is_superuser=True"):
        User.objects.create_superuser(
            email="admin@example.com", password="secret123", is_superuser=False
        )