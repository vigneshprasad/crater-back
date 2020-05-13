from rest_framework.permissions import BasePermission

from community.posts.models import Post
from community.posts.services import get_post


class PostPermission(BasePermission):
    """
    Allows detail info managing for specific user.
    """
    def has_permission(self, request, view):
        if request.method == 'DELETE':
            try:
                return get_post(view.kwargs['pk']).creator == request.user
            except Post.DoesNotExist:
                return False
        return True
