from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed


class IsAuthenticated(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            raise AuthenticationFailed
        # if not request.user.email_verified:
        #     raise AuthenticationFailed
        return True


class AllowAny(permissions.BasePermission):
    """
    Allows access to all user's, authenticated or otherwise.

    """
    def has_permission(self, request, view):
        return True
