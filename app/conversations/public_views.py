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
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.GroupWebinarSerializer
    queryset = models.Group.objects.filter(closed=False, type=constants.GROUP_TYPE_WEBINAR_ENUM)
    permission_classes = [permissions.AllowAny]

    def _get_group_queryset(self, is_live):
        """
        Return live webinars if `is_live` is set to True
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

    def _create_data_by_date(self, queryset):
        data = []
        date_list = list(queryset.values_list("start__date", flat=True).distinct())
        date_list.reverse()

        for date in date_list:
            objects = queryset.filter(
                start__date=date,
            )
            serialized = self.get_serializer(objects, many=True)
            data.append({
                "date": date.isoformat(),
                "groups": serialized.data,
            })
        return data

    @action(
        methods=["GET"],
        detail=False,
    )
    def upcoming(self, request):
        queryset = self._get_group_queryset(is_live=False)
        date_list = list(queryset.values_list("start__date", flat=True).distinct())
        date_list.reverse()
        data = self._create_data_by_date(queryset=queryset)
        return Response(data)

    @action(
        methods=["GET"],
        detail=False,
    )
    def live(self, request):
        queryset = self._get_group_queryset(is_live=True)
        date_list = list(queryset.values_list("start__date", flat=True).distinct())
        date_list.reverse()
        data = self._create_data_by_date(queryset=queryset)
        return Response(data)

    @action(
        methods=["POST"],
        detail=False,
    )
    def is_live(self, request):
        """
        Webhook request to set `is_live` field for webinar group
        """
        data = request.data
        # TODO(Sanjeev): Verify webhook using signature

        meeting_details = data.get("meeting")
        participant_details = data.get("participant")

        participant = services.get_dyte_meeting_participant(
            meeting_id=meeting_details.get("id"),
            user_uuid=participant_details.get("clientSpecificId")
        )

        if participant is not None:
            group = participant.dyte_meeting.group
            if str(group.host.uuid) == participant_details.get("clientSpecificId"):
                group.is_live = True
                group.save()

        return Response("OK", status.HTTP_200_OK)

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

        if participant is not None:
            group = participant.dyte_meeting.group
            if str(group.host.uuid) != participant_details.get("clientSpecificId"):
                participant.is_online = True
                participant.save()

        return Response("OK", status.HTTP_200_OK)

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

        if participant is not None:
            group = participant.dyte_meeting.group
            if str(group.host.uuid) != participant_details.get("clientSpecificId"):
                participant.is_online = False
                participant.save()

        return Response("OK", status.HTTP_200_OK)
