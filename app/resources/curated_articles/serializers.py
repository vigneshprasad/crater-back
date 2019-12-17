from rest_framework import serializers

from resources.curated_articles.models import Tag, SourceWebsite, CuratedArticle


class CuratedArticleSerializer(serializers.ModelSerializer):
    tag = serializers.CharField(source='tag.name')
    website = serializers.CharField(source='website.name')
    website_url = serializers.CharField(source='website.url')

    class Meta:
        model = CuratedArticle
        fields = (
            'pk',
            'title',
            'text',
            'picture',
            'tag',
            'website',
            'website_url',
            'created',
        )


class ArticleTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'pk',
            'name',
        )


class ArticleWebsiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = SourceWebsite
        fields = (
            'pk',
            'name',
            'url',
        )

