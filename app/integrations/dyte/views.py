import logging

from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from conversations import models as conversation_models
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
    def started(self, request):
        """Webhook for meeting started from Dyte meeting.

        Note:
            Fires as soon as first person joins the meeting.

        """
        data = request.data
        dyte_meeting_details = data.get("meeting")
        dyte_meeting_id = dyte_meeting_details.get("id")

        group = private.get_group_for_dyte_meeting_id(dyte_meeting_id=dyte_meeting_id)
        # If the dyte meeting is not found, return a not acceptable response
        if not group:
            LOGGER.error("Dyte meeting ID doesn't exist: {}".format(dyte_meeting_id))
            return Response(status=status.HTTP_200_OK)

        # Mark the session active once people are on the meeting.
        group.session_active = True
        group.save()

        return Response(status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[user_permissions.AllowAny]
    )
    def ended(self, request):
        """Webhook for meeting end from Dyte meeting.

        Note:
            Fires after 1 minute of everyone leaving the stream
                or if the host ends meeting for all.

        """
        data = request.data
        dyte_meeting_details = data.get("meeting")

        dyte_meeting_id = dyte_meeting_details.get("id")
        group = private.get_group_for_dyte_meeting_id(dyte_meeting_id=dyte_meeting_id)
        # If the dyte meeting is not found, return a not acceptable response
        if not group:
            LOGGER.error("Dyte meeting ID doesn't exist: {}".format(dyte_meeting_id))
            return Response(status=status.HTTP_200_OK)

        # Update the session state for a group.
        group.session_active = False
        group.save()

        # If the time is less that group start, return 200.
        if not timezone.now() > group.start:
            return Response(status=status.HTTP_200_OK)

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

        # If the user can't join the group, return from here.
        if not group.can_join_group(user):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Determine the preset based on the user and group.
        preset = private.get_preset_for_group(user, group)
        # Add participant to the meeting.
        dyte_participant = public.add_participant_to_meeting(
            group.dyte_meeting,
            user,
            preset
        )
        serialized = self.get_serializer(dyte_participant)
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
            LOGGER.error("Participant not in Dyte meeting: {}".format(user_pk))
            return Response(status=status.HTTP_200_OK)

        group = participant.dyte_meeting.group
        # Mark the participant online.
        participant.mark_online()

        # If the participant is not host, return from here.
        if group.host_id != user_pk:
            return Response(status=status.HTTP_200_OK)

        # If the group host has joined mark meeting as
        # live.
        group.mark_live(user=participant.participant)

        # Start recording the session if required.
        if not group.can_start_recording():
            return Response(status=status.HTTP_200_OK)

        tasks.start_recording_for_meeting_if_required.apply_async(
            args=(group.id,),
            countdown=5
        )
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
            LOGGER.error("Participant not in Dyte meeting: {}".format(user_pk))
            return Response(status=status.HTTP_200_OK)

        group = participant.dyte_meeting.group
        # Mark the participant offline.
        participant.mark_offline()

        # If the participant is not host, return from here.
        if group.host_id != user_pk:
            return Response(status=status.HTTP_200_OK)

        # Mark the group inactive if host leaves the meeting.
        group.mark_inactive(user=participant.participant)
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

        dyte_meeting_recording = private.get_dyte_meeting_recording_for_recording_id(recording_id=recording_id)
        if not dyte_meeting_recording:
            LOGGER.error("Dyte meeting recording not found: {}".format(recording_id))
            return Response(status=status.HTTP_200_OK)

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
    # TODO(Nishant): Change this to active only.
    def meeting_active_livestream(self, request, pk, *args, **kwargs):
        """Returns active livestream for a group.

        Note:
            pk provided is the group's ID we are getting the
                livestream for.

        """
        try:
            group = conversation_models.Group.objects.get(id=pk)
        except conversation_models.Group.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Get active live stream for the group.
        livestream = public.get_livestream_for_stream_and_status(
            group,
            status=constants.LIVE_STREAM_STATUS_LIVE
        )
        if not livestream:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(livestream)
        return Response(serialized.data, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False,
        permission_classes=[user_permissions.AllowAny]
    )
    def status(self, request, *args, **kwargs):
        """Updates status of a livestream object from Dyte's
            end.

        """
        data = request.data
        stream_id = data.get("streamId")
        livestream_status = data.get("status")
        livestream = private.get_livestream_object_for_stream_id(stream_id=stream_id)
        if not livestream:
            LOGGER.error("Live stream ID doesn't exist: {}".format(stream_id))
            return Response(status=status.HTTP_200_OK)

        # Update livestream status for stream id.
        livestream.update_status(livestream_status)
        return Response(status=status.HTTP_200_OK)
