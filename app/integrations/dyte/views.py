import datetime

import pytz
from rest_framework import status
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from integrations.dyte import private
from integrations.dyte import models
from integrations.dyte import serializers
from integrations.dyte import public
from integrations.dyte import constants
from conversations import models as conversation_models

from users import permissions


class DyteMeetingViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.DyteMeeting.objects.all()
    serializer_class = serializers.DyteMeetingSerializer

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[permissions.AllowAny]
    )
    def ended(self, request):
        """Webhook for meeting end from Dyte meeting."""

        data = request.data
        # TODO(Sanjeev): Verify webhook using signature
        dyte_meeting_details = data.get("meeting")

        dyte_meeting_id = dyte_meeting_details.get("id")
        dyte_meeting = private.get_dyte_meeting_for_dyte_meeting_id(
            dyte_meeting_id=dyte_meeting_id
        )

        # If the dyte meeting is not for a group return.
        group = dyte_meeting.group if dyte_meeting else None
        if not group:
            return Response(status=status.HTTP_200_OK)

        utc = pytz.utc
        if datetime.datetime.now(tz=utc) > group.start:
            # Mark group as closed on meeting end.
            group.mark_closed(user=group.host)

        return Response(status=status.HTTP_200_OK)


class DyteParticipantViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.DyteMeetingParticipant.objects.all()
    serializer_class = serializers.DyteParticipantSerializer

    @action(
        methods=["POST"],
        detail=True
    )
    def connect(self, request, *args, **kwargs):
        """This request creates auth token for people who are
            joining into the call.

        Note:
             This is will create auth token for every user again
                regarded of whether it's expired.

        """
        group_id = kwargs.get("pk")
        user = request.user

        try:
            group = conversation_models.Group.objects.get(pk=group_id)
        except conversation_models.Group.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        dyte_meeting = group.dyte_webinar.first()
        if not dyte_meeting:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if (group.host.pk == user.pk) or (user in group.speakers.all()):
            # Add the host to the dyte meeting.
            result = public.add_participant_to_meeting(
                dyte_meeting,
                user,
                constants.DEFAULT_WEBINAR_HOST_PRESET_NAME
            )
        else:
            # Add other participants to the dyte meeting.
            result = public.add_participant_to_meeting(
                dyte_meeting,
                user
            )

        serialized = self.get_serializer(result)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Returns a dyte participant for user and group_id."""
        group_id = kwargs.get("pk")
        user = request.user

        participant = private.get_participant_for_user_and_group_id(
            user=user,
            group_id=group_id
        )
        if not participant:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(participant)
        return Response(serialized.data, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[permissions.AllowAny]
    )
    def joined(self, request):
        """Webhook from dyte if a participant joins a dyte call.

         Note:
             Fires everytime a participant joins a call.

         """

        data = request.data
        # TODO(Sanjeev): Verify webhook using signature
        dyte_meeting_details = data.get("meeting")
        dyte_participant_details = data.get("participant")

        dyte_meeting_id = dyte_meeting_details.get("id")
        user_pk = dyte_participant_details.get("clientSpecificId")

        # If the user_pk is not in the participant list
        # for the dyte meeting, return.
        participant = private.get_participant_for_user_id_and_dyte_meeting_id(
            user_pk=user_pk,
            dyte_meeting_id=dyte_meeting_id
        )
        if not participant:
            return Response(status=status.HTTP_200_OK)

        # If the group is not present or the group doesn't
        # have a host return 200. If the group is
        # marked closed, don't make it live.
        group = participant.dyte_meeting.group
        if group and group.closed:
            return Response(status=status.HTTP_200_OK)

        if group.host.uuid.__str__() == user_pk:
            # If the group host has joined mark meeting as
            # live.
            group.mark_live(user=participant.participant)

            # Start recording the session if there are
            # no active recordings for the live stream.
            active_recordings = private.get_active_recording_for_dyte_meeting(
                dyte_meeting=participant.dyte_meeting
            )
            if not active_recordings:
                public.start_recording_for_group(group)

        # Mark the participant online.
        participant.mark_online()

        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[permissions.AllowAny]
    )
    def left(self, request):
        """Webhook from dyte if a participant leave a dyte call.

        Note:
            Fires everytime a participant leaves a call.

        """

        data = request.data
        # TODO(Sanjeev): Verify webhook using signature
        dyte_meeting_details = data.get("meeting")
        dyte_participant_details = data.get("participant")

        dyte_meeting_id = dyte_meeting_details.get("id")
        user_pk = dyte_participant_details.get("clientSpecificId")

        # If the user_pk is not in the participant list
        # for the dyte meeting, return.
        participant = private.get_participant_for_user_id_and_dyte_meeting_id(
            user_pk=user_pk,
            dyte_meeting_id=dyte_meeting_id
        )
        if not participant:
            return Response(status=status.HTTP_200_OK)

        # If the group is not present or the group doesn't
        # have a host return 200.
        group = participant.dyte_meeting.group
        if not (group and group.host):
            return Response(status=status.HTTP_200_OK)

        # If the group host has joined mark meeting as
        # not live/inactive.
        if group.host.uuid.__str__() == user_pk:
            group.mark_inactive(user=participant.participant)

        # Mark the participant offline.
        participant.mark_offline()

        return Response(status=status.HTTP_200_OK)


class DyteMeetingRecordingViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.DyteMeetingRecording.objects.all()
    serializer_class = serializers.DyteMeetingRecordingSerializer

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[permissions.AllowAny]
    )
    def status(self, request):
        """Webhook from dyte if there is a status update for
            a meeting recording.

        """
        data = request.data
        # TODO(Sanjeev): Verify webhook using signature

        dyte_recording_details = data.get("recording")

        recording_id = dyte_recording_details.get("recordingId")
        recording_status = dyte_recording_details.get("status")
        started_at = dyte_recording_details.get("startedTime")
        stopped_at = dyte_recording_details.get("stoppedTime")

        dyte_meeting_recording = private.get_dyte_meeting_recording_for_recording_id(
            recording_id=recording_id
        )
        if not dyte_meeting_recording:
            return Response(status=status.HTTP_200_OK)

        # Update recording status only if it has changed.
        if dyte_meeting_recording.status == recording_status:
            return Response(status=status.HTTP_200_OK)

        # Update the status and start and stopped times.
        dyte_meeting_recording.status = recording_status

        try:
            dyte_meeting_recording.started_at = datetime.datetime.strptime(
                started_at, constants.DYTE_DATETIME_FORMAT
            ) if started_at else None
            dyte_meeting_recording.stopped_at = datetime.datetime.strptime(
                stopped_at, constants.DYTE_DATETIME_FORMAT
            ) if stopped_at else None
        except ValueError:
            dyte_meeting_recording.started_at = None
            dyte_meeting_recording.stopped_at = None

        dyte_meeting_recording.save()

        return Response(status=status.HTTP_200_OK)
