from django.urls import path, include
from rest_framework.routers import DefaultRouter

from resources.events.views import EventViewSet, RSVPDViewSet, CommentViewSet

app_name = 'resources'

router = DefaultRouter()
router.register('events', EventViewSet)
router.register('rsvpd', RSVPDViewSet)
router.register('comments', CommentViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
