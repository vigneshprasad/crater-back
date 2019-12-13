from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from community.comments.paginators import CommentPagination
from community.comments.serializers import CommentSerializer
from community.comments.services import get_comments
from resources.events.filters import EventFilter
from resources.events.models import RSVPD, Event
from resources.events.paginators import EventPagination
from resources.events.serializers import EventSerializer, RSVPDSerializer
from resources.events.services import get_events, get_event


class EventViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = EventSerializer
    pagination_class = EventPagination
    queryset = get_events().prefetch_related('event_comments', 'rsvpds').all()
    permission_classes = (IsAuthenticated,)
    filterset_class = EventFilter


class RSVPDViewSet(mixins.CreateModelMixin, GenericViewSet):
    serializer_class = RSVPDSerializer
    queryset = RSVPD.objects.all()
    permission_classes = (IsAuthenticated,)


class CommentViewSet(mixins.CreateModelMixin, DestroyModelMixin, GenericViewSet):
    serializer_class = CommentSerializer
    queryset = get_comments()
    pagination_class = CommentPagination
    permission_classes = (IsAuthenticated,)

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated],
        detail=True
    )
    def event(self, request, pk):
        try:
            queryset = self.filter_queryset(get_event(pk).event_comments.all()[2:])
        except Event.DoesNotExist:
            raise NotFound
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
