from rest_framework import views, generics, permissions, response
from django.shortcuts import get_object_or_404
from .models import Quiz, QuizAttempt, QuizAnswer, Question, Choice
from .serializers import QuizSer, AttemptSubmitSer, AttemptResultSer, QuestionSer, ChoiceSer
from .grading import grade_attempt
#-----------------------------------#  
# Quiz create and view
class QuizDetailView(generics.ListAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSer
    permission_classes = [permissions.IsAuthenticated]
class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.all()
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    serializer_class = QuizSer
# Quiz retrieve, update and delete
class QuizRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    serializer_class = QuizSer
    lookup_field = 'id'
#-----------------------------------#  
# Question create and view
class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSer
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    def get_queryset(self):
        quiz_id = self.kwargs.get('quiz_id')
        return Question.objects.filter(quiz_id=quiz_id)
    def perform_create(self, serializer):
        quiz_id = self.kwargs.get('quiz_id')
        quiz = get_object_or_404(Quiz, id=quiz_id)
        serializer.save(quiz=quiz)
# Question retrieve, update and delete
class QuestionRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = QuestionSer
    lookup_field = 'id'
#-----------------------------------#
# Choice create and view 
class ChoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ChoiceSer
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    def get_queryset(self):
        question_id = self.kwargs.get('question_id')
        return Choice.objects.filter(question_id=question_id)
    def perform_create(self, serializer):
        question_id = self.kwargs.get('question_id')
        question = get_object_or_404(Question, id=question_id)
        serializer.save(question=question)
# Choice retrieve, update and delete
class ChoiceRetrieveUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Choice.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ChoiceSer
    lookup_field = 'id'

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
