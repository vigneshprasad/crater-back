from rest_framework import serializers

from . import models


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.City
        fields = ('pk', 'name')
