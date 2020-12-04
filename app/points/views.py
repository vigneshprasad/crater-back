from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from users import permissions
from .models import UserPoints, PointsRule
from rewards.services import get_max_rewards_rs_conversion
from points import serializers
from points import constants


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
        max_conversion = get_max_rewards_rs_conversion()
        response_data = {
            'points': user_points.points,
            'money_value': user_points.points * max_conversion
        }
        return Response(response_data)


class PointsRuleViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = serializers.PointsRuleSerializer
    queryset = PointsRule.objects.filter(key__in=constants.RULES_KEYS_FOR_API)
    permission_classes = [permissions.IsAuthenticated]