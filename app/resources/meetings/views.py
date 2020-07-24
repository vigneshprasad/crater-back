from rest_framework.response import Response
from rest_framework import mixins, viewsets

from users import permissions
from resources.meetings import models
from resources.meetings import serializers


class MeetingViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        instance = self.get_queryset().filter(is_active=True).first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserMeetingPreferenceViewSet(mixins.CreateModelMixin,
                                   mixins.UpdateModelMixin,
                                   viewsets.GenericViewSet):
    serializer_class = serializers.UserMeetingPreferenceSerializer
    queryset = models.UserMeetingPreference.objects.all()
    permission_classes = [permissions.IsAuthenticated]
