from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from cryptography.fernet import InvalidToken

from users import permissions
from resources.meetings import models, choices, serializers, services


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
        if not objective:
            return request
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

class PastUserMeetingPreferenceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.PastUserMeetingPreferenceSerializer
    queryset = models.MeetingPreference.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        instance = models.MeetingPreference.objects.filter(user=user).last()
        if not instance:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        serialized = self.get_serializer(instance)
        return Response(serialized.data)


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


class MeetingRSVPViewSet(viewsets.GenericViewSet):
    serializer_class = serializers.MeetingRSVPSerializer
    queryset = models.MeetingRSVP.objects.all()
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['POST'],
        detail=False,
    )
    def attending(self, request):
        data = request.data.get('meeting')

        if not data:
            return self.generate_bad_request({
                'error': 'Query data missing',
            })

        try:
            user, meeting = services.get_user_meeting_from_url(data)
            rsvp = models.MeetingRSVP.objects.get(
                meeting=meeting,
                participant=user,
            )
            rsvp.status = choices.MEETING_RSVP_STATUS_CHOICES[0][0]
            rsvp.save()
            serialized = self.get_serializer(rsvp)
            return Response(data=serialized.data)

        except InvalidToken:
            return self.generate_bad_request({
                'error': 'Incorrect query string',
            })
        except models.MeetingRSVP.DoesNotExist:
            return self.generate_bad_request({
                'error': 'Meeting not found',
            })
        except models.Meeting.DoesNotExist:
            return self.generate_bad_request({
                'error': 'User not found',
            })

