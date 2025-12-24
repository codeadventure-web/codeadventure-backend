from django.contrib import admin
from django import forms
from .models import Language, Problem, TestCase, Submission


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("key", "id")
    search_fields = ("key",)


class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is the first row in the inline formset and it's a new record,
        # default 'hidden' to False.
        if self.instance._state.adding and self.prefix == "testcases-0":
            self.fields["hidden"].initial = False


class TestCaseInline(admin.TabularInline):
    model = TestCase
    form = TestCaseForm
    extra = 1
    fields = ("input_data", "expected_output", "hidden")
    show_change_link = True


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "time_limit_ms", "memory_limit_mb", "created_at")
    list_editable = ("time_limit_ms", "memory_limit_mb")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [TestCaseInline]
    filter_horizontal = ("allowed_languages",)
    save_as = True


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ("problem", "hidden", "created_at")
    list_filter = ("hidden", "problem")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "problem", "language", "status", "created_at")
    list_filter = ("status", "language", "problem")
    search_fields = ("id", "user__username", "problem__slug")
    date_hierarchy = "created_at"
