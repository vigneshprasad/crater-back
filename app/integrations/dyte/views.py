from rest_framework import status
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from integrations.dyte import models
from integrations.dyte import serializers
from integrations.dyte import public
from integrations.dyte import constants
from conversations import models as conversation_models

from users import permissions


class DyteParticipantViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.DyteMeetingParticipant.objects.all()
    serializer_class = serializers.DyteParticipantSerializer

    @action(methods=["POST"], detail=True)
    def connect(self, request, *args, **kwargs):
        """This request creates auth token for people who are
            joining into the call.

        Note:
             This is will create auth token for every user again
                regarded of whether it's expired.

        """
        pk = kwargs.get("pk")
        user = request.user

        try:
            group = conversation_models.Group.objects.get(pk=pk)
        except conversation_models.Group.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        dyte_meeting = group.dyte_webinar.first()
        if not dyte_meeting:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if group.host.pk == user.pk:
            # Add the host to the dyte meeting.
            result = public.add_participant_to_meeting(
                dyte_meeting,
                user,
                constants.DEFAULT_WEBINAR_HOST_PRESET_NAME
            )
        else:
            # Add other participants to the dyte meeting.
            result = public.add_participant_to_meeting(
                dyte_meeting.dyte_meeting,
                user
            )

        serialized = self.get_serializer(result)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """Returns a dyte participant for user."""
        pk = kwargs.get("pk")
        user = request.user

        try:
            dyte_meeting_participant = self.get_queryset().get(
                participant=user,
                dyte_meeting__group_id=pk,
            )
        except models.DyteMeetingParticipant.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(dyte_meeting_participant)
        return Response(serialized.data, status=status.HTTP_200_OK)
