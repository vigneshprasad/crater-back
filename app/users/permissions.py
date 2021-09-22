import base64
import hmac
import json
import hashlib

from django.conf import settings

from rest_framework import permissions, exceptions
from rest_framework.exceptions import AuthenticationFailed


class IsAuthenticated(permissions.BasePermission):
    """Allows access only to authenticated users."""

    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            raise AuthenticationFailed

        return True


class AllowAny(permissions.BasePermission):
    """Allows access to all user's, authenticated or otherwise."""
    def has_permission(self, request, view):
        return True


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """The request is authenticated as a user, or is a read-only request."""

    def has_permission(self, request, view):
        if request.method in settings.SAFE_METHODS:
            return True

        if not bool(request.user and request.user.is_authenticated):
            raise AuthenticationFailed

        return True


class HasActiveSubscription(permissions.BasePermission):
    """Allows access only to authenticated users."""

    def has_permission(self, request, view):
        if not bool(request.user and request.user.has_active_subscription):
            raise exceptions.PermissionDenied

        return True


class SegmentRequest(permissions.BasePermission):
    """Allows access only to segment webhooks.

    TODO(Nishant): Use this for segment webhooks after testing.

    """

    def has_permission(self, request, view):
        signature = request.headers.get("x-signature")
        if not signature:
            return True

        # Generate the signature and verify the segment signature.
        key = bytes(settings.SEGMENT_SHARED_SECRET, "UTF-8")
        message = bytes(json.dumps(request.body), "UTF-8")
        digester = hmac.new(key, message, hashlib.sha1)
        digest = digester.digest()
        generated_signature = str(base64.urlsafe_b64encode(digest), "UTF-8")

        if not signature == generated_signature:
            raise exceptions.PermissionDenied

        return True

