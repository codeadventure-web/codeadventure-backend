from rest_framework import views, generics, permissions, response
from django.shortcuts import get_object_or_404
from .models import Quiz, QuizAttempt, QuizAnswer, Question, Choice
from .serializers import (
    QuizSer,
    AttemptSubmitSer,
    AttemptResultSer,
    QuestionSer,
    ChoiceSer,
)
from .grading import grade_attempt
from rest_framework.exceptions import NotFound
import uuid

# -----------------------------------#
# Quiz create and view
class QuizDetailView(generics.ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"


class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSer


# Quiz retrieve, update and delete
# class QuizRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Quiz.objects.all()
#     serializer_class = QuizSer
#     lookup_field = "id"

class QuizRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QuizSer

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        # Ép kiểu lesson_id thành UUID để chắc chắn match đúng
        try:
            lesson_uuid = uuid.UUID(lesson_id)
        except ValueError:
            raise NotFound(detail="Invalid lesson ID format.")
        
        return Quiz.objects.filter(lesson_id=lesson_uuid)  # Dùng lesson_id thay vì lesson__id

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            obj = queryset.get()
            self.check_object_permissions(self.request, obj)
            return obj
        except Quiz.DoesNotExist:
            raise NotFound(detail="Quiz not found for this lesson.")


# -----------------------------------#
# Question create and view
class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSer

    def get_queryset(self):
        quiz_id = self.kwargs.get("quiz_id")
        return Question.objects.filter(quiz_id=quiz_id)

    def create(self, serializer):
        quiz_id = self.kwargs.get("quiz_id")
        quiz = get_object_or_404(Quiz, id=quiz_id)
        serializer.save(quiz=quiz)


# Question retrieve, update and delete
class QuestionRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSer
    lookup_field = "id"


# -----------------------------------#
# Choice create and view
class ChoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ChoiceSer

    def get_queryset(self):
        question_id = self.kwargs.get("question_id")
        return Choice.objects.filter(question_id=question_id)

    def create(self, serializer):
        question_id = self.kwargs.get("question_id")
        question = get_object_or_404(Question, id=question_id)
        serializer.save(question=question)


# Choice retrieve, update and delete
class ChoiceRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSer
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


class AttemptResultView(generics.RetrieveAPIView):
    queryset = QuizAttempt.objects.all()
    serializer_class = AttemptResultSer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
