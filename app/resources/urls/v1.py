from django.urls import path, include
from rest_framework.routers import DefaultRouter

from resources.curated_articles.views import TagViewSet, CuratedArticleViewSet, WebsiteViewSet
from resources.events.views import EventViewSet, RSVPDViewSet, CommentViewSet

app_name = 'resources'

router = DefaultRouter()
router.register('events', EventViewSet)
router.register('rsvpd', RSVPDViewSet)
router.register('comments', CommentViewSet)
router.register('articles', CuratedArticleViewSet)
router.register('tags', TagViewSet)
router.register('websites', WebsiteViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
