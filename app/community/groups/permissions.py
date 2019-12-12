from rest_framework.permissions import BasePermission


class GroupPermission(BasePermission):
    """
    Allows access authorized user to group.
    """
    def has_permission(self, request, view):
        return view.kwargs['pk'] in request.user.user_groups.all()
