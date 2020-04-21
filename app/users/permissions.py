from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed


class IsAuthenticated(permissions.BasePermission):
    """
    Allows access only to authenticated users.
    """
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            raise AuthenticationFailed
        email_address = request.user.emailaddress_set.first()
        if email_address and not email_address.verified:
            raise AuthenticationFailed
        return True
