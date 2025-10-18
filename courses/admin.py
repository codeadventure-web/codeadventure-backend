from django.contrib import admin
from .models import Course, Section, Lesson, Enrollment, Progress

for m in (Course, Section, Lesson, Enrollment, Progress):
    admin.site.register(m)
