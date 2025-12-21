from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTeacherOrReadOnly(BasePermission):
    """
    GET, HEAD, OPTIONS: cho tất cả
    POST, PUT, PATCH, DELETE: chỉ user đăng nhập & is_staff
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAdminOrReadOnly(BasePermission):
    """Allow read-only for everyone, write only for admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        # Check for authenticated user and admin role
        return (
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class IsOwner(BasePermission):
    """Only allow access to objects belonging to the requesting user."""

    def has_object_permission(self, request, view, obj):
        # Assumes the model instance 'obj' has a 'user' attribute.
        return obj.user == request.user
