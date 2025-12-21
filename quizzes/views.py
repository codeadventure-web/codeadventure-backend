from rest_framework import views, generics, permissions, response
from django.shortcuts import get_object_or_404
from .models import Quiz, QuizAttempt, QuizAnswer, Question
from .serializers import (
    QuizSer, 
    AttemptSubmitSer, 
    AttemptResultSer, 
    QuestionSer
)
from .grading import grade_attempt

class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSer

class QuizRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSer
    lookup_field = "id"

class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSer
    def get_queryset(self):
        return Question.objects.filter(quiz_id=self.kwargs.get("quiz_id"))
    def create(self, serializer):
        quiz = get_object_or_404(Quiz, id=self.kwargs.get("quiz_id"))
        serializer.save(quiz=quiz)

class QuestionRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSer
    lookup_field = "id"

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