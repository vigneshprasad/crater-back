from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from users import permissions
from .models import UserPoints


class UserPointsViewSet(GenericViewSet):
    queryset = UserPoints.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @action(
        methods=['GET'],
        detail=False
    )
    def my(self, request):
        user = request.user
        user_points = UserPoints.objects.get(user=user)
        response_data = {
            'points': user_points.points
        }
        return Response(response_data)