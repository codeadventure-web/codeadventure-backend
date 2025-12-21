from django.contrib import admin
from .models import Quiz, QuizAttempt

for m in (Quiz, QuizAttempt):
    admin.site.register(m)
