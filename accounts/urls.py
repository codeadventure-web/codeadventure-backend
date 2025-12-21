from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    MeView,
    health,
    SafeLogoutView,
    ForgotPasswordView,
    ResetPasswordView,
    GoogleLoginView,
    GithubLoginView,
)

urlpatterns = [
    path("logout/", SafeLogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("health/", health, name="health"),
    path("password/forgot/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("password/reset/", ResetPasswordView.as_view(), name="reset_password"),
    path("social/google/", GoogleLoginView.as_view(), name="social_google"),
    path("social/github/", GithubLoginView.as_view(), name="social_github"),
]
