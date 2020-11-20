from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from users import permissions
from .models import UserPoints
from rewards.models import Package


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
        packages = Package.objects.filter(is_active=True)
        max_conversion = 0
        for package in packages:
            if package.points_conversion > max_conversion:
                max_conversion = package.points_conversion
        response_data = {
            'points': user_points.points,
            'money_value': user_points.points * max_conversion
        }
        return Response(response_data)