import datetime

from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from conversations import paginators
from conversations import serializers
from conversations import models
from conversations import constants
from conversations import services
from users import permissions


class GroupWebinarPublicViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupWebinarSerializer
    queryset = models.Group.objects.filter(closed=False, type=constants.GROUP_TYPE_WEBINAR_ENUM)
    permission_classes = [permissions.AllowAny]
    filterset_fields = []

    def _get_upcoming_webinars(self):
        """Return upcoming webinars."""
        return self.get_queryset().filter(
                is_live=False,
                start__gte=datetime.datetime.now()
            )

    def _get_live_webinars(self):
        """Return live webinars."""
        return self.get_queryset().filter(
            is_live=True
        )

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

        if not page:
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
        methods=["POST"],
        detail=False,
    )
    def is_live(self, request):
        """Webhook request to set `is_live` field for webinar group"""

        data = request.data
        # TODO(Sanjeev): Verify webhook using signature

        meeting_details = data.get("meeting")
        participant_details = data.get("participant")

        participant = services.get_dyte_meeting_participant(
            meeting_id=meeting_details.get("id"),
            user_uuid=participant_details.get("clientSpecificId")
        )

        if not participant:
            return Response(status=status.HTTP_200_OK)

        group = participant.dyte_meeting.group
        if str(group.host.uuid) == participant_details.get("clientSpecificId"):
            group.is_live = True
            group.save()

        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
    )
    def participant_joined(self, request):

        data = request.data
        # TODO(Sanjeev): Verify webhook using signature

        meeting_details = data.get("meeting")
        participant_details = data.get("participant")

        participant = services.get_dyte_meeting_participant(
            meeting_id=meeting_details.get("id"),
            user_uuid=participant_details.get("clientSpecificId")
        )
        if not participant:
            return Response(status=status.HTTP_200_OK)

        group = participant.dyte_meeting.group
        if str(group.host.uuid) != participant_details.get("clientSpecificId"):
            participant.is_online = True
            participant.save()

        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
    )
    def participant_left(self, request):

        data = request.data
        # TODO(Sanjeev): Verify webhook using signature

        meeting_details = data.get("meeting")
        participant_details = data.get("participant")

        participant = services.get_dyte_meeting_participant(
            meeting_id=meeting_details.get("id"),
            user_uuid=participant_details.get("clientSpecificId")
        )

        if not participant:
            return Response(status=status.HTTP_200_OK)

        group = participant.dyte_meeting.group
        if str(group.host.uuid) != participant_details.get("clientSpecificId"):
            participant.is_online = False
            participant.save()

        return Response(status=status.HTTP_200_OK)
