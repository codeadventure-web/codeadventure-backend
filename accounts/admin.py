from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile


# Define an inline admin descriptor for Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"


# Define a new User admin
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")

    # Add 'role' to the fieldsets
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("role",)}),)


# Re-register User with CustomUserAdmin
admin.site.register(User, CustomUserAdmin)

# Edit Profiles separately
admin.site.register(Profile)
