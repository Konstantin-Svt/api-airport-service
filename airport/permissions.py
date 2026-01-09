from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if (request.method in SAFE_METHODS) or (
            request.user and request.user.is_staff
        ):
            return True
        return False


class AuthenticatedReadCreate(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.method in (
            "POST",
            "GET",
            "OPTIONS",
            "HEAD",
        ):
            return True
        return False
