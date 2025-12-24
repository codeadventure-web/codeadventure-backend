from django.contrib import admin
from django import forms
from .models import Quiz, Question, Choice


class ChoiceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        is_answer_count = 0
        for form in self.forms:
            if not form.is_valid():
                continue
            if form.cleaned_data.get("is_answer") and not form.cleaned_data.get(
                "DELETE"
            ):
                is_answer_count += 1

        if is_answer_count > 1:
            raise forms.ValidationError(
                "Only one choice can be marked as the correct answer."
            )


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    formset = ChoiceInlineFormSet


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz")
    list_filter = ("quiz",)
    search_fields = ("text",)
    inlines = [ChoiceInline]


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True
    # 'text' is the only field in Question besides quiz, but StackedInline makes it larger.


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "id", "created_at")
    search_fields = ("title",)
    inlines = [QuestionInline]
