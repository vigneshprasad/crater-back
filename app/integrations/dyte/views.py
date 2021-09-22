from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from integrations.dyte import models
from integrations.dyte import serializers

from users import permissions


class DyteParticipantViewSet(
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.DyteMeetingParticipant.objects.all()
    serializer_class = serializers.DyteParticipantSerializer

    def retrieve(self, request, *args, **kwargs):

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
