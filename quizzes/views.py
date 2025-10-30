from rest_framework import views, generics, permissions, response
from django.shortcuts import get_object_or_404
from .models import Quiz, QuizAttempt, QuizAnswer
from .serializers import QuizSer, AttemptSubmitSer, AttemptResultSer
from .grading import grade_attempt


class QuizDetailView(generics.RetrieveAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "lesson_id"


class AttemptStartView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, lesson_id):
        quiz = get_object_or_404(Quiz, lesson_id=lesson_id)
        att = QuizAttempt.objects.create(user=request.user, quiz=quiz)
        return response.Response({"attempt_id": str(att.id)})


class AttemptSubmitView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, attempt_id):
        att = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
        ser = AttemptSubmitSer(data=request.data)
        ser.is_valid(raise_exception=True)
        QuizAnswer.objects.filter(attempt=att).delete()
        for a in ser.validated_data["answers"]:
            QuizAnswer.objects.create(attempt=att, **a)
        grade_attempt(att)
        return response.Response(AttemptResultSer(att).data)


class AttemptResultView(generics.RetrieveAPIView):
    queryset = QuizAttempt.objects.all()
    serializer_class = AttemptResultSer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
