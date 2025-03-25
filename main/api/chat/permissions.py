from rest_framework import permissions

class AllowAll(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

