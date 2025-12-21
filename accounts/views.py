import os
import redis
from django.db import connection
from .serializers import (
    UserMeSerializer,
    RegisterSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    GoogleLoginSerializer,
    GithubLoginSerializer,
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


@extend_schema(tags=["Auth"], responses={200: OpenApiTypes.OBJECT})
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

    @extend_schema(tags=["Auth"], summary="Register a new user")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Auth"], summary="Get or update current user info")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=["Auth"])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=["Auth"])
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
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset."}, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=GoogleLoginSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Login with Google",
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


class GithubLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=GithubLoginSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Login with GitHub",
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