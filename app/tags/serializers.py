from rest_framework import serializers

from . import models


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = ('pk', 'name')


class MasterClassTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MasterClassTag
        fields = (
            'pk', 'name'
        )


class ArticleTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ArticleTag
        fields = ('pk', 'name')


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Company
        fields = ('pk', 'name')


class FundingSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Funding
        fields = ('pk', 'name')


class IndustrySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Industry
        fields = ('pk', 'name')
