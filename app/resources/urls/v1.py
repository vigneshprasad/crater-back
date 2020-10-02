from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

from resources.curated_articles.views import CuratedArticleViewSet
from resources.events.views import EventViewSet, RSVPDViewSet, CommentViewSet
from resources.masterclasses.views import MaterClassViewSet
from resources.meetings import views as meeting_views
from resources.meetings import public_views as meeting_public_views

app_name = 'resources'

router = DefaultRouter()
router.register('events', EventViewSet)
router.register('rsvpd', RSVPDViewSet)
router.register('comments', CommentViewSet)
router.register('articles', CuratedArticleViewSet)
router.register('masterclasses', MaterClassViewSet)
router.register('meetings', meeting_views.MeetingConfigViewSet)
router.register('meeting-preferences', meeting_views.UserMeetingPreferenceViewSet)

public_url_patters = [
    path(
        'meetings',
        meeting_public_views.MeetingViewSetPublicViewSet.as_view(
            {'get': 'list', 'post': 'create'}
        )
    ),
    path(
        'meetings/preference',
        meeting_public_views.UserMeetingPreferencePublicViewSet.as_view(
            {'get': 'list', 'post': 'create'}
        )
    ),
    path(
        'meetings/communication',
        meeting_public_views.MeetingCommunicationViewSet.as_view(
            {'get': 'send_intro_emails', 'post': 'send_intro_emails'}
        )
    )
]

urlpatterns = [
    path('', include(router.urls)),
    path('public/', include(public_url_patters))
]
