from django.urls import path, include
from rest_framework.routers import DefaultRouter

from resources.curated_articles.views import CuratedArticleViewSet
from resources.events.views import EventViewSet, RSVPDViewSet, CommentViewSet
from resources.masterclasses.views import MaterClassViewSet
from resources.meetings import views as meeting_views

app_name = 'resources'

router = DefaultRouter()
router.register('events', EventViewSet)
router.register('rsvpd', RSVPDViewSet)
router.register('comments', CommentViewSet)
router.register('articles', CuratedArticleViewSet)
router.register('masterclasses', MaterClassViewSet)
router.register('meetings', meeting_views.MeetingViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
