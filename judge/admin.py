from django.contrib import admin
from .models import Language, Problem, TestCase, Submission

for m in (Language, Problem, TestCase, Submission):
    admin.site.register(m)
