import os
import redis
from django.db import connection
from django.http import HttpResponseRedirect
from .serializers import (
    UserMeSerializer,
    RegisterSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    GoogleLoginSerializer,
    GithubLoginSerializer,
    LoginResponseSerializer,
)
from rest_framework import generics, status, throttling, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes


# Throttle for login attempts
class LoginRateThrottle(throttling.UserRateThrottle):
    scope = "login"


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.get_username()
        token["email"] = getattr(user, "email", "") or ""
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data.update(
            {
                "user": {
                    "id": str(self.user.pk),
                    "username": self.user.get_username(),
                    "email": getattr(self.user, "email", "") or "",
                }
            }
        )
        return data


@extend_schema(
    tags=["Auth"],
    summary="Login (JWT)",
    description="Authenticates a user with username and password. Returns a pair of JWT tokens (access and refresh) along with basic user information. The access token should be used in the Authorization header as 'Bearer <token>'.",
    request=LoginSerializer,
    responses={200: LoginResponseSerializer},
    examples=[
        OpenApiExample(
            "Login example",
            request_only=True,
            value={"username": "dao", "password": "pass1234"},
        )
    ],
)
class LoginView(TokenObtainPairView):
    """POST username/password → access, refresh, user info"""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    serializer_class = LoginSerializer


@extend_schema(
    tags=["Auth"],
    responses={200: OpenApiTypes.OBJECT},
    summary="Health check",
    description="Check the health status of the backend, including Database and Redis connectivity. Returns 200 OK even if degraded, but 'status' field will reflect the health.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    ok_db = ok_redis = True
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
    except Exception:
        ok_db = False
    try:
        r = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_timeout=1.5
        )
        r.ping()
    except Exception:
        ok_redis = False
    data = {
        "status": "ok" if (ok_db and ok_redis) else "degraded",
        "db": ok_db,
        "redis": ok_redis,
    }
    resp = Response(data, status=status.HTTP_200_OK)
    resp["Cache-Control"] = "public, max-age=5"
    return resp


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        description="Creates a new user account with a hashed password. Returns the username and email upon successful registration.",
        responses={201: RegisterSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Get current user info",
        description="Retrieves the profile and account details of the currently authenticated user.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=["Auth"],
        summary="Update current user info",
        description="Updates the profile and account details of the currently authenticated user (Full update).",
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        tags=["Auth"],
        summary="Partially update current user info",
        description="Updates specific fields of the currently authenticated user's profile or account.",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class SafeLogoutView(APIView):
    """
    POST {"refresh": "<refresh_token>"}
    - Blacklists the refresh token if valid
    - Returns 205 even if token is already blacklisted/invalid (idempotent logout)
    - No Authorization header required
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=inline_serializer(
            name="LogoutRequest", fields={"refresh": serializers.CharField()}
        ),
        responses={205: None},
        summary="Logout (blacklist refresh token)",
        description="Blacklists the provided refresh token to prevent further access. This endpoint is idempotent and returns 205 Reset Content even if the token is already invalid.",
    )
    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Missing 'refresh'."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except (InvalidToken, TokenError):
            # Treat as already logged out / invalid -> still succeed
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=ForgotPasswordSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Request password reset email",
        description="Sends a password reset email to the user if the email address exists in the system. Always returns a successful response to prevent user enumeration.",
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # always return success to avoid user enumeration
        return Response(
            {"detail": "If that email exists, we've sent reset instructions."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=ResetPasswordSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Reset password using token",
        description="Resets the user's password using the UID and token sent via email.",
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password has been reset."}, status=status.HTTP_200_OK
        )


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=GoogleLoginSerializer,
        responses={200: LoginResponseSerializer},
        summary="Login with Google",
        description="Exchange a Google ID Token for a JWT pair. If the user doesn't exist, a new account will be created automatically.",
    )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create_or_get_user()

        # issue JWT using SimpleJWT
        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.pk,
                "username": user.username,
                "email": user.email,
            },
            "provider": "google",
        }
        return Response(data, status=status.HTTP_200_OK)


class GoogleLoginRedirectView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Get Google Login URL",
        description="Redirects to Google's OAuth2 login page.",
    )
    def get(self, request):
        from .services import get_google_auth_url
        return HttpResponseRedirect(get_google_auth_url())


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Google OAuth Callback",
        description="Handles the callback from Google, exchanges code for token, logs in user, and redirects to frontend.",
    )
    def get(self, request):
        from .services import google_get_access_token
        from .serializers import GoogleLoginSerializer
        from django.conf import settings
        from django.shortcuts import redirect

        code = request.query_params.get("code")
        if not code:
            return Response({"error": "Code not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_data = google_get_access_token(code)
            id_token_str = token_data.get("id_token")
            
            # Reuse existing logic
            serializer = GoogleLoginSerializer(data={"id_token": id_token_str})
            serializer.is_valid(raise_exception=True)
            user = serializer.create_or_get_user()

            refresh = RefreshToken.for_user(user)
            
            # Redirect to frontend with tokens
            frontend_url = settings.FRONTEND_URL
            return redirect(f"{frontend_url}/auth/success?access={str(refresh.access_token)}&refresh={str(refresh)}")
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GithubLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=GithubLoginSerializer,
        responses={200: LoginResponseSerializer},
        summary="Login with GitHub",
        description="Exchange a GitHub Access Token for a JWT pair. If the user doesn't exist, a new account will be created automatically.",
    )
    def post(self, request):
        serializer = GithubLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create_or_get_user()

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.pk,
                "username": user.username,
                "email": user.email,
            },
            "provider": "github",
        }
        return Response(data, status=status.HTTP_200_OK)


class GithubLoginRedirectView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Get GitHub Login URL",
        description="Redirects to GitHub's OAuth2 login page.",
    )
    def get(self, request):
        from .services import get_github_auth_url
        return HttpResponseRedirect(get_github_auth_url())


class GithubCallbackView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="GitHub OAuth Callback",
        description="Handles the callback from GitHub, exchanges code for token, logs in user, and redirects to frontend.",
    )
    def get(self, request):
        from .services import github_get_access_token
        from .serializers import GithubLoginSerializer
        from django.conf import settings
        from django.shortcuts import redirect

        code = request.query_params.get("code")
        if not code:
            return Response({"error": "Code not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_data = github_get_access_token(code)
            access_token = token_data.get("access_token")
            
            # Reuse existing logic
            serializer = GithubLoginSerializer(data={"access_token": access_token})
            serializer.is_valid(raise_exception=True)
            user = serializer.create_or_get_user()

            refresh = RefreshToken.for_user(user)
            
            # Redirect to frontend with tokens
            frontend_url = settings.FRONTEND_URL
            return redirect(f"{frontend_url}/auth/success?access={str(refresh.access_token)}&refresh={str(refresh)}")
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
