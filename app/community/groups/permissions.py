from rest_framework.permissions import BasePermission

from community.posts.services import get_post


class GroupPermission(BasePermission):
    """
    Allows access authorized user to the group.
    """
    def has_permission(self, request, view):
        group_ids = request.user.user_groups.filter(is_approved=True).values_list('group', flat=True)
        return int(view.kwargs['pk']) in group_ids


class GroupPostPermission(GroupPermission):
    """
    Allows access to make likes for authorized user in group posts or posts without any group.
    """
    def has_permission(self, request, view):
        post_id = request.data.get('post') or view.kwargs['pk']
        group_ids = request.user.user_groups.filter(is_approved=True).values_list('group', flat=True)
        return not get_post(post_id).group or get_post(post_id).group.id in group_ids
