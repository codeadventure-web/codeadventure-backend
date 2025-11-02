import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="pass1234",
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()
