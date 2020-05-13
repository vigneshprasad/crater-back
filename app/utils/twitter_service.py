import twitter
from django.conf import settings

api = twitter.Api(
    consumer_key=settings.TWITTER_CUSTOMER_API_KEY,
    consumer_secret=settings.TWITTER_CUSTOMER_API_SECRET_KEY,
    access_token_key=settings.TWITTER_ACCESS_TOKEN,
    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
)

#
# class TweetSerializer(serializers.Serializer):
#     text = serializers.CharField()
#     lang = serializers.CharField()
#     avatar = serializers.URLField(source='user.profile_image_url_https')
#     name = serializers.CharField(source='user.name')
#     verified = serializers.BooleanField(source='user.verified')
#     screen_name = serializers.CharField(source='user.screen_name')
#     created = serializers.CharField(source='created_at')
#     media_url = serializers.CharField(source='media.media_url_https', allow_null=True)
#     media_type = serializers.CharField(source='media.type', allow_null=True)
#     retweet_count = serializers.IntegerField()
#     favorite_count = serializers.IntegerField()

