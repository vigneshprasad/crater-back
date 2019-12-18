from django.urls import path, include
from rest_framework.routers import DefaultRouter

from resources.curated_articles.views import CuratedArticleViewSet, WebsiteViewSet
from resources.events.views import EventViewSet, RSVPDViewSet, CommentViewSet
from resources.masterclasses.views import MaterClassViewSet

app_name = 'resources'

router = DefaultRouter()
router.register('events', EventViewSet)
router.register('rsvpd', RSVPDViewSet)
router.register('comments', CommentViewSet)
router.register('articles', CuratedArticleViewSet)
router.register('websites', WebsiteViewSet)
router.register('masterclasses', MaterClassViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
