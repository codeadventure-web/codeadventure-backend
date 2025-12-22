from django.contrib import admin
from .models import Course, Lesson, Progress, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ("title", "order", "type", "problem", "quiz")
    autocomplete_fields = ["problem", "quiz"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "created_at")
    list_filter = ("is_published", "tags")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "type", "problem", "quiz")
    list_filter = ("course", "type")
    list_editable = ("order",)
    search_fields = ("title", "content_md")
    ordering = ("course", "order")
    autocomplete_fields = ["course", "problem", "quiz"]
    readonly_fields = ("slug",)


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "status", "updated_at")
    list_filter = ("status", "lesson__course")
    search_fields = ("user__username", "lesson__title")
