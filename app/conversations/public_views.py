import datetime

from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

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

    def _get_group_queryset(self, is_live):
        """Return live webinars if `is_live` is set to True
            else return upcoming webinars

        """

        now = datetime.datetime.now()
        if is_live:
            queryset = self.get_queryset().filter(
                is_live=True,
            )
        else:
            queryset = self.get_queryset().filter(
                is_live=False,
                start__gte=now
            )
        return queryset

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
        queryset = self.filter_queryset(self._get_group_queryset(
            is_live=False
        )).order_by("-start")
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
        queryset = self.filter_queryset(self._get_group_queryset(
            is_live=True
        )).order_by("-start")
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        filterset_fields=["host"],
    )
    def all(self, request):
        queryset_live = self._get_group_queryset(is_live=True)
        queryset_upcoming = self._get_group_queryset(is_live=False)
        queryset = self.filter_queryset(queryset_live | queryset_upcoming)
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
