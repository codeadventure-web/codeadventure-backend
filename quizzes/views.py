from rest_framework import generics, permissions, views, response
from django.shortcuts import get_object_or_404
from .models import Quiz, QuizAttempt
from .serializers import (
    QuizSerializer,
    AttemptSubmitSerializer,
    AttemptResultSerializer
)
from .grading import grade_attempt

class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class QuizRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    lookup_field = "id"
    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

class AttemptStartView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user
        )
        return response.Response({
            "attempt_id": str(attempt.id)
        })

class AttemptSubmitView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            QuizAttempt,
            id=attempt_id,
            user=request.user
        )
        serializer = AttemptSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt.answers = serializer.validated_data["answers"]
        grade_attempt(attempt)
        return response.Response(
            AttemptResultSerializer(attempt).data
        )
