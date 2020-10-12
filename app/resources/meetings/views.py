from rest_framework.response import Response
from rest_framework import mixins, viewsets, status

from users import permissions
from resources.meetings import models
from resources.meetings import serializers
from resources.meetings import choices


class MeetingConfigViewSet(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = serializers.MeetingConfigSerializer
    queryset = models.Config.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        instance = self.get_queryset().filter(
            is_active=True,
            is_registration_open=True
        ).last()
        # If there is no active meeting with registration open
        # return and empty response.
        if not instance:
            return Response({})

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserMeetingPreferenceViewSet(mixins.ListModelMixin,
                                   mixins.RetrieveModelMixin,
                                   mixins.CreateModelMixin,
                                   mixins.UpdateModelMixin,
                                   viewsets.GenericViewSet):
    serializer_class = serializers.UserMeetingPreferenceSerializer
    queryset = models.MeetingPreference.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        active_meeting = models.Config.objects.filter(
            is_active=True,
            is_registration_open=True
        ).last()
        if not active_meeting:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        instance = active_meeting.user_preferences.filter(user=user).last()
        if not instance:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        serialized = self.get_serializer(instance)
        return Response(serialized.data)

    def _add_objectives_to_request(self):
        request = self.request
        objective = request.data.get('objective')
        if objective:
            for choice in choices.OBJECTIVE_CHOICES:
                if choice[0] == objective:
                    try:
                        objective_model = models.Objective.objects.get(name=choice[1], is_active=True)
                        request.data['objectives'] = [objective_model.pk]
                    except models.Objective.DoesNotExist:
                        pass
        return request

    def update(self, request, *args, **kwargs):
        request = self._add_objectives_to_request()
        return super(UserMeetingPreferenceViewSet, self).update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request = self._add_objectives_to_request()
        return super(UserMeetingPreferenceViewSet, self).create(request, *args, **kwargs)


class MeetingViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.meeting_set.all()


class MeetingObjectivesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.MeetingObjectiveSerializer
    queryset = models.Objective.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]


class MeetingInterestsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.MeetingInterestSerializer
    queryset = models.Interest.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]


class MeetingConfigV2ViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.MeetingConfigV2Serializer
    queryset = models.Config.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        instance = self.get_queryset().filter(
            is_active=True,
            is_registration_open=True
        ).last()
        if not instance:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        serialized = self.get_serializer(instance)
        return Response(serialized.data)
