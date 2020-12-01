from rest_framework import serializers

from points import models


class PointsRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PointsRule
        fields = (
            'key',
            'desc',
            'points_value',
        )
