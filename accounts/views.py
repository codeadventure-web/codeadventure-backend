from rest_framework import generics, permissions
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserMeSerializer
from django.db import connection
import os
import redis
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


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
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
    except Exception:
        ok_redis = False
    return Response(
        {
            "status": "ok" if (ok_db and ok_redis) else "degraded",
            "db": ok_db,
            "redis": ok_redis,
        }
    )


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class HealthView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"})
