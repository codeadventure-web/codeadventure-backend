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
    GoogleLoginRedirectView,
    GoogleCallbackView,
    GithubLoginRedirectView,
    GithubCallbackView,
)

urlpatterns = [
    path("logout/", SafeLogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("health/", health, name="health"),
    path("password/forgot/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("password/reset/", ResetPasswordView.as_view(), name="reset_password"),
    path("google/", GoogleLoginView.as_view(), name="social_google"),
    path("google/login/", GoogleLoginRedirectView.as_view(), name="social_google_login"),
    path("google/callback/", GoogleCallbackView.as_view(), name="social_google_callback"),
    path("github/", GithubLoginView.as_view(), name="social_github"),
    path("github/login/", GithubLoginRedirectView.as_view(), name="social_github_login"),
    path("github/callback/", GithubCallbackView.as_view(), name="social_github_callback"),
]
