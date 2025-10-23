from django.contrib import admin
from .models import Course, Section, Lesson, Progress, Tag


# A custom admin for the new Tag model
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


# A custom admin for Course to show tags
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)  # Makes picking tags easier


# Register models
admin.site.register(Course, CourseAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Section)
admin.site.register(Lesson)
admin.site.register(Progress)
