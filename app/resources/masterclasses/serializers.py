from rest_framework import serializers

from resources.masterclasses.models import MasterClass
from tags.serializers import MasterClassTagSerializer


class MasterClassSerializer(serializers.ModelSerializer):
    tags = MasterClassTagSerializer(many=True)
    thumbnail = serializers.CharField(source='file.cover_thumbnail', allow_null=True)
    cover = serializers.SerializerMethodField()

    class Meta:
        model = MasterClass
        fields = (
            'pk',
            'created',
            'author',
            'position',
            'thumbnail',
            'description',
            'cover',
            'tags'
        )

    @staticmethod
    def get_cover(masterclass):
        if masterclass.file:
            return masterclass.file.cover_transcoder
        if masterclass.cover:
            return masterclass.cover.url
