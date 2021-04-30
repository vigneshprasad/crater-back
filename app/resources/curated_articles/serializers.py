from rest_framework import serializers

from resources.curated_articles.models import CuratedArticle
from tags import serializers as tag_serializer


class CuratedArticleSerializer(serializers.ModelSerializer):
    tag = serializers.CharField(source="tag.name")
    picture = serializers.ImageField(source="image", read_only=True)
    website_tag = serializers.CharField(source="website_tag.name")
    website_tag_detail = tag_serializer.ArticleWebsiteSerializer(source="website_tag", read_only=True)

    class Meta:
        model = CuratedArticle
        fields = (
            "pk",
            "title",
            "description",
            "image",
            "tag",
            "website_tag",
            "website_url",
            "website_tag_detail",
            "picture"
        )
