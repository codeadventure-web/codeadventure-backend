from django.urls import path
from .views import *

urlpatterns = [
    path("quizzes/", QuizListCreateView.as_view()),
    path("quizzes/<uuid:id>/", QuizRetrieveUpdateDelete.as_view()),
    path("attempts/start/<uuid:quiz_id>/", AttemptStartView.as_view()),
    path("attempts/submit/<uuid:attempt_id>/", AttemptSubmitView.as_view()),
]
