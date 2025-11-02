import pytest
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


@pytest.mark.django_db
def test_user_str():
    u = User.objects.create_user(username="dao", password="x")
    assert str(u) == "dao"


@pytest.mark.django_db
def test_profile_auto_created_on_user_create():
    u = User.objects.create_user(username="dao2", password="x")
    profile = Profile.objects.get(user=u)
    assert profile.user == u


@pytest.mark.django_db
def test_profile_str():
    u = User.objects.create_user(username="dao3", password="x")
    p = u.profile
    assert "dao3" in str(p)
