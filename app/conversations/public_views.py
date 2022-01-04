import datetime

from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from conversations import constants
from conversations import paginators
from conversations import models
from conversations import serializers
from conversations import services
from conversations import signals
from users import permissions as user_permissions


class GroupWebinarPublicViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupWebinarSerializer
    queryset = models.Group.objects.filter(type=constants.GROUP_TYPE_WEBINAR_ENUM, is_published=True)
    permission_classes = [user_permissions.AllowAny]
    filterset_fields = ["categories"]

    def _get_upcoming_webinars(self):
        """Return upcoming webinars."""
        return self.get_queryset().filter(
                is_live=False,
                closed=False,
                start__gte=datetime.datetime.now()
            )

    def _get_live_webinars(self):
        """Return live webinars."""
        return self.get_queryset().filter(
            is_live=True,
            closed=False
        )

    def _get_past_webinars_with_recordings(self):
        """Return past webinars with published recordings."""

        groups_with_recordings = self.get_queryset().filter(
            start__lte=datetime.datetime.now(),
            recording__isnull=False
        )
        # Get group with recording objects which are published
        # and have recording object present.
        published_groups_with_recording = groups_with_recordings.filter(
            recording__recording__isnull=False,
            recording__is_published=True
        ).order_by("-recording__order")

        return published_groups_with_recording

    def _get_featured_webinars(self):
        """Return featured webinars.

        Note:
            Only featured webinars in the future will
                show up. Also if a featured webinar is
                live don't show in this list.

        """
        min_start = datetime.datetime.now() - datetime.timedelta(hours=1)
        return self.get_queryset().filter(
            is_featured=True,
            is_live=False,
            closed=False,
            start__gte=min_start
        )

    @action(
        methods=["GET"],
        pagination_class=paginators.FeaturedWebinarPagination,
        detail=False,
        filterset_fields=["host"]
    )
    def featured(self, request):
        """Return list of webinars that has to featured for Crater club.

        Note:
            Returns list of live and featured webinars.

        """
        live_groups = self.filter_queryset(self._get_live_webinars())
        featured_groups = self.filter_queryset(self._get_featured_webinars())

        live_and_featured_groups = self.filter_queryset(
            live_groups | featured_groups
        ).order_by("-is_live", "start")
        page = self.paginate_queryset(live_and_featured_groups)

        if page is None:
            serializer = self.get_serializer(live_and_featured_groups, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["GET"],
        detail=False,
        filterset_fields=["host"]
    )
    def upcoming(self, request):
        """Return webinars which are in the future.

        Note:
            Return groups queryset sorted by start of
            the groups.

        """
        queryset = self.filter_queryset(self._get_upcoming_webinars()).order_by("start")
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        filterset_fields=["host"]
    )
    def live(self, request):
        """Return webinars which are in live right now.

        Note:
            Return groups queryset sorted by start of
            the groups.

        """
        queryset = self.filter_queryset(self._get_live_webinars()).order_by("start")
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        filterset_fields=["host"],
    )
    def all(self, request):
        """Return all webinars live and upcoming."""

        queryset_live = self._get_live_webinars()
        queryset_upcoming = self._get_upcoming_webinars()

        queryset = self.filter_queryset(
            queryset_live | queryset_upcoming
        ).order_by("-live", "start")
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        pagination_class=paginators.WebinarPagination,
        detail=False,
        filterset_fields=["host"],
    )
    def past(self, request):
        """Returns past webinars with published recordings."""

        queryset = self.filter_queryset(
            self._get_past_webinars_with_recordings()
        )

        page = self.paginate_queryset(queryset)

        if page is None:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
