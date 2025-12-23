from django.contrib import admin
from .models import Quiz, Question, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz")
    list_filter = ("quiz",)
    search_fields = ("text",)
    inlines = [ChoiceInline]


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "id", "created_at")
    search_fields = ("title",)
    inlines = [QuestionInline]
