import uuid

import pytest
from django.db import IntegrityError

from apps.users.models import User


def test_username_field_is_email():
    assert User.USERNAME_FIELD == "email"


def test_required_fields_is_empty():
    assert User.REQUIRED_FIELDS == []


def test_username_is_removed_from_model():
    assert User.username is None


@pytest.mark.django_db
def test_primary_key_is_uuid():
    user = User.objects.create_user(email="test@example.com", password="secret123")
    assert isinstance(user.pk, uuid.UUID)


@pytest.mark.django_db
def test_is_email_verified_defaults_to_false():
    user = User.objects.create_user(email="test@example.com", password="secret123")
    assert user.is_email_verified is False


@pytest.mark.django_db
def test_email_unique_constraint_raises_on_duplicate():
    User.objects.create_user(email="test@example.com", password="secret123")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="test@example.com", password="other123")