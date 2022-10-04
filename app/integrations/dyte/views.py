import datetime
import logging

import pytz
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from conversations import constants as conversation_constants, models as conversation_models, \
    public as conversation_public
from integrations.dyte import constants, models, private, public, serializers, tasks
from users import permissions as user_permissions

LOGGER = logging.getLogger(__name__)


class DyteMeetingViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    queryset = models.DyteMeeting.objects.all()
    serializer_class = serializers.DyteMeetingSerializer

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[user_permissions.AllowAny]
    )
    def ended(self, request):
        """Webhook for meeting end from Dyte meeting.

        Note:
            Fires after 2 minutes of everyone leaving the stream
                or if the host ends meeting for all.

        """

        data = request.data
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
    permission_classes = [user_permissions.IsAuthenticated]
    queryset = models.DyteMeetingParticipant.objects.only(
        "dyte_meeting",
        "participant",
        "auth_token"
    ).select_related(
        "dyte_meeting__group"
        "dyte_meeting__group__host"
        "dyte_meeting__group__speakers"
    )
    serializer_class = serializers.DyteParticipantSerializer

    @action(
        methods=["POST"],
        detail=True
    )
    def connect(self, request, *args, **kwargs):
        """This request creates auth token for people who are
            joining into the call.

        Note:
             This will create auth token for every user again
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

        # Determine the preset based on whether the stream is
        # happening via OBS.
        is_obs = group.is_obs
        host_preset = constants.DEFAULT_WEBINAR_HOST_PRESET_NAME \
            if not is_obs else constants.WEBINAR_OBS_HOST_PRESET_NAME
        participant_preset = constants.DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME \
            if not is_obs else constants.WEBINAR_OBS_PARTICIPANT_PRESET_NAME

        if group.privacy == conversation_constants.GROUP_PRIVACY_PRIVATE_ENUM and not\
                conversation_public.check_if_attendee_in_group:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if (group.host_id == user.pk) or (user in group.speakers.all()):
            result = public.add_participant_to_meeting(
                dyte_meeting,
                user,
                host_preset
            )
        else:
            result = public.add_participant_to_meeting(
                dyte_meeting,
                user,
                participant_preset
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
        permission_classes=[user_permissions.AllowAny]
    )
    def joined(self, request):
        """Webhook from dyte if a participant joins a dyte call.

         Note:
             Fires everytime a participant joins a call.

         """
        data = request.data
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
            # Start recording the session if required.
            if group.can_start_recording():
                tasks.start_recording_for_meeting_if_required.apply_async(
                    args=(group.id,),
                    countdown=5
                )

        # Mark the participant online.
        participant.mark_online()

        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[user_permissions.AllowAny]
    )
    def left(self, request):
        """Webhook from dyte if a participant leave a dyte call.

        Note:
            Fires everytime a participant leaves a call.

        """
        data = request.data
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
        if not participant.is_offline():
            participant.mark_offline()

        return Response(status=status.HTTP_200_OK)


class DyteMeetingRecordingViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [user_permissions.IsAuthenticated]
    queryset = models.DyteMeetingRecording.objects.all()
    serializer_class = serializers.DyteMeetingRecordingSerializer

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[user_permissions.AllowAny]
    )
    def status(self, request):
        """Webhook from dyte if there is a status update for
            a meeting recording.

        """
        data = request.data
        dyte_recording_details = data.get("recording")

        recording_id = dyte_recording_details.get("id")
        recording_status = dyte_recording_details.get("status")
        started_at = dyte_recording_details.get("startedTime")
        stopped_at = dyte_recording_details.get("stoppedTime")
        file_size = dyte_recording_details.get("fileSize") or 0
        file_size_mb = round(file_size / (1024 * 1024), 2)

        dyte_meeting_recording = private.get_dyte_meeting_recording_for_recording_id(
            recording_id=recording_id
        )
        if not dyte_meeting_recording:
            LOGGER.error("Dyte meeting recording not found: {}".format(recording_id))
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        # Update recording status only if it has changed.
        if dyte_meeting_recording.status == recording_status:
            return Response(status=status.HTTP_200_OK)

        # Update the status and start and stopped times.
        dyte_meeting_recording.status = recording_status
        dyte_meeting_recording.file_size = file_size_mb
        dyte_meeting_recording.save()
        # Update start and stop times.
        dyte_meeting_recording.update_start_and_stop_times(started_at, stopped_at)
        return Response(status=status.HTTP_200_OK)


class LiveStreamViewSet(mixins.UpdateModelMixin, GenericViewSet):
    permission_classes = [user_permissions.IsAuthenticated]
    queryset = models.LiveStream.objects.all()
    serializer_class = serializers.LiveStreamSerializer

    def update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(
        methods=["GET"],
        detail=True
    )
    def meeting_active_livestream(self, request, pk, *args, **kwargs):
        try:
            livestream = models.LiveStream.objects.get(
                dyte_meeting__group_id=pk,
                status=constants.LIVE_STREAM_STATUS_LIVE
            )
        except models.LiveStream.DoesNotExist:
            public.get_active_livestream_for_webinar(pk)
            return Response(status=status.HTTP_404_NOT_FOUND)
        serialized = self.get_serializer(livestream)
        return Response(serialized.data, status=status.HTTP_200_OK)
