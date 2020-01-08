from rest_framework import serializers

from . import models


class ExchangeCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExchangeCategory
        fields = [
            'pk',
            'name'
        ]
