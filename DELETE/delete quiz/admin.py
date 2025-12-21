from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, QuizAnswer

for m in (Quiz, Question, Choice, QuizAttempt, QuizAnswer):
    admin.site.register(m)
