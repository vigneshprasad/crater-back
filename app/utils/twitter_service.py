import twitter
from django.conf import settings

api = twitter.Api(
    consumer_key=settings.TWITTER_CUSTOMER_API_KEY,
    consumer_secret=settings.TWITTER_CUSTOMER_API_SECRET_KEY,
    access_token_key=settings.TWITTER_ACCESS_TOKEN,
    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET
)
