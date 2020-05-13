from rest_framework import serializers

from resources.curated_articles.models import CuratedArticle


class CuratedArticleSerializer(serializers.ModelSerializer):
    tag = serializers.CharField(source='tag.name')
    website_tag = serializers.CharField(source='website_tag.name')

    class Meta:
        model = CuratedArticle
        fields = (
            'pk',
            'title',
            'text',
            'picture',
            'tag',
            'website_tag',
            'website_url',
            'created',
        )
