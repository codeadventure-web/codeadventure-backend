from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt, QuizAnswer


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


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "is_passed", "finished", "created_at")
    list_filter = ("is_passed", "finished", "quiz")
    search_fields = ("user__username", "quiz__title")


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_choice_ids")
    list_filter = ("question__quiz",)
