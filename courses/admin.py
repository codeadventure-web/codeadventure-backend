from django.contrib import admin
from .models import Course, Lesson, Progress, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ("title", "order", "type")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "created_at")
    list_filter = ("is_published", "tags")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "type")
    list_filter = ("course", "type")
    search_fields = ("title", "content_md")
    ordering = ("course", "order")


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "status", "updated_at")
    list_filter = ("status", "lesson__course")
    search_fields = ("user__username", "lesson__title")
