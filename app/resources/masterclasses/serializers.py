from rest_framework import serializers

from resources.masterclasses.models import MasterClass
from tags.serializers import MasterClassTagSerializer


class MasterClassSerializer(serializers.ModelSerializer):
    tags = MasterClassTagSerializer(many=True)

    class Meta:
        model = MasterClass
        fields = (
            'pk',
            'author',
            'position',
            'description',
            'cover',
            'tags'
        )
