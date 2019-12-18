from rest_framework import serializers

from . import models
from .models import MasterClassTag, ArticleTag


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = ('pk', 'name')


class MasterClassTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = MasterClassTag
        fields = (
            'pk', 'name'
        )


class ArticleTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArticleTag
        fields = ('pk', 'name')
