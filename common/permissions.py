from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Allow read-only for everyone, write only for admins."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwner(BasePermission):
    """Only allow access to objects belonging to the requesting user."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
