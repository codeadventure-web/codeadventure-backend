from django.contrib import admin
from .models import Course, Lesson, Progress, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    fields = ("title", "order", "type", "content_md", "problem", "quiz")
    autocomplete_fields = ["problem", "quiz"]
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "created_at")
    list_filter = ("is_published", "tags")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [LessonInline]


from django.urls import reverse
from django.utils.html import format_html

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "type", "edit_content_link")
    list_filter = ("course", "type")
    list_editable = ("order",)
    search_fields = ("title", "content_md")
    ordering = ("course", "order")
    autocomplete_fields = ["course", "problem", "quiz"]
    readonly_fields = ("slug", "edit_content_link")

    def edit_content_link(self, obj):
        if obj.type == "QUIZ" and obj.quiz:
            url = reverse("admin:quizzes_quiz_change", args=[obj.quiz.id])
            return format_html('<a href="{}">Edit Quiz "{}"</a>', url, obj.quiz.title)
        elif obj.type == "JUDGE" and obj.problem:
            url = reverse("admin:judge_problem_change", args=[obj.problem.id])
            return format_html('<a href="{}">Edit Problem "{}"</a>', url, obj.problem.title)
        return "-"
    edit_content_link.short_description = "Related Content"


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "status", "updated_at")
    list_filter = ("status", "lesson__course")
    search_fields = ("user__username", "lesson__title")
