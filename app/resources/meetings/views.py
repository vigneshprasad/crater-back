import datetime
import pytz

from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from cryptography.fernet import InvalidToken
from freelance.settings import TIME_ZONE

from users import permissions
from resources.meetings import models, choices, serializers, services
from resources.meetings import signals


class MeetingConfigViewSet(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = serializers.MeetingConfigSerializer
    queryset = models.Config.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        instance = services.get_latest_active_meeting_config()
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

    @action(
        methods=['GET'],
        detail=False,
    )
    def past(self, request):
        user = request.user
        instance = models.MeetingPreference.objects.filter(user=user).last()
        if not instance:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        config = services.get_latest_active_meeting_config()
        slot_start_times = list(instance.time_slots.all().values_list('start_time', flat=True).distinct())
        instance.time_slots.set(config.available_time_slots.all().filter(start_time__in=slot_start_times))
        serialized = self.get_serializer(instance)
        return Response(serialized.data)

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
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response_serializer = serializers.UserMeetingPreferenceSerializer(instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(response_serializer.data)

    def create(self, request, *args, **kwargs):
        request = self._add_objectives_to_request()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response_serializer = serializers.UserMeetingPreferenceSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        # Send a signal on new preference creation.
        signals.new_meeting_registration.send(
            sender=instance.__class__,
            preference=instance
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return serializers.PostUserMeetingPreferenceSerializer
        else:
            return serializers.UserMeetingPreferenceSerializer


class MeetingViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.meeting_set.filter(is_canceled=False)

    def _get_meeting_queryset(self, is_past):
        now = datetime.datetime.now()
        if is_past:
            queryset = self.get_queryset().filter(
                start__lte=now,
            )
        else:
            queryset = self.get_queryset().filter(
                start__gte=now,
            )
        return queryset

    def _create_data_by_date(self, queryset):
        data = []
        date_list = list(queryset.values_list('start__date', flat=True).distinct())
        date_list.reverse()

        for date in date_list:
            objects = queryset.filter(
                start__date=date,
            )
            serialized = self.get_serializer(objects, many=True)
            data.append({
                'date': date.isoformat(),
                'meetings': serialized.data,
            })
        return data

    @action(
        methods=['GET'],
        detail=False,
    )
    def upcoming(self, request):
        queryset = self._get_meeting_queryset(is_past=False)
        date_list = list(queryset.values_list('start__date', flat=True).distinct())
        date_list.reverse()
        data = self._create_data_by_date(queryset=queryset)
        return Response(data)

    @action(
        methods=['GET'],
        detail=False,
    )
    def past(self, request):
        queryset = self._get_meeting_queryset(is_past=True)
        date_list = list(queryset.values_list('start__date', flat=True).distinct())
        date_list.reverse()
        data = self._create_data_by_date(queryset=queryset)
        return Response(data)


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
        instance = services.get_latest_active_meeting_config()
        if not instance:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        serialized = self.get_serializer(instance)
        return Response(serialized.data)


class MeetingRSVPViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingRSVPSerializer
    queryset = models.MeetingRSVP.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['POST'],
        detail=False,
        permission_classes=[permissions.AllowAny]
    )
    def attending(self, request):
        """Check if the user is attending the meeting and mark it.

        Note:
            This is a public view which gets user and meeting id from
                a encoded string in the body and marks the user
                as attending for the meeting.

        """
        data = request.data.get('meeting')
        if not data:
            return self.generate_bad_request(
                {'error': 'Query data missing'}
            )

        try:
            user, meeting = services.get_user_meeting_from_url(data)
            if meeting.status == choices.MEETING_STATUS_CANCELLED:
                return self.generate_bad_request({
                    'error': 'This meeting has been cancelled. Please contact WorkNetwork if you think this is a mistake.'
                })
            rsvp = models.MeetingRSVP.objects.get(
                meeting=meeting,
                participant=user,
            )
            rsvp.status = choices.MEETING_RSVP_STATUS_CHOICES[0][0]
            rsvp.save()
            serialized = self.get_serializer(rsvp)
            return Response(data=serialized.data)

        except InvalidToken:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )
        except models.MeetingRSVP.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )
        except models.Meeting.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )

    @action(
        methods=['POST'],
        detail=False,
    )
    def confirmed(self, request, *args, **kwargs):
        request_data = request.data
        meeting_id = request_data.get("meeting")
        participant = request.user

        try:
            rsvp = models.MeetingRSVP.objects.get(
                meeting_id=meeting_id,
                participant=participant
            )
        except models.MeetingRSVP.DoesNotExist:
            return self.generate_bad_request(
                {"error": "User doesn't have an RSVP for meeting."}
            )
        except models.MeetingRSVP.MultipleObjectsReturned:
            return self.generate_bad_request(
                {"error": "User has multiple RSVP for meeting."}
            )

        rsvp.status = choices.MEETING_RSVP_STATUS_ATTENDING
        rsvp.save()

        # Send a signal which updates the status after RSVP is
        # updated.
        signals.rsvp_status_updated.send(
            sender=rsvp.__class__,
            user=request.user,
            rsvp=rsvp
        )
        serialized = self.get_serializer(rsvp)
        return Response(data=serialized.data)

    @action(
        methods=['POST'],
        detail=False,
    )
    def cancelled(self, request, *args, **kwargs):
        request_data = request.data
        meeting_id = request_data.get("meeting")
        participant = request.user

        try:
            rsvp = models.MeetingRSVP.objects.get(
                meeting_id=meeting_id,
                participant=participant
            )
        except models.MeetingRSVP.DoesNotExist:
            return self.generate_bad_request(
                {"error": "User doesn't have an RSVP for meeting."}
            )
        except models.MeetingRSVP.MultipleObjectsReturned:
            return self.generate_bad_request(
                {"error": "User has multiple RSVP for meeting."}
            )

        rsvp.status = choices.MEETING_RSVP_STATUS_NOT_ATTENDING
        rsvp.save()

        # Send a signal which updates the status after RSVP is
        # updated.
        signals.rsvp_status_updated.send(
            sender=rsvp.__class__,
            user=request.user,
            rsvp=rsvp
        )
        serialized = self.get_serializer(rsvp)
        return Response(data=serialized.data)

    @action(
        methods=['POST'],
        detail=False,
        serializer_class=serializers.PostRescheduleRequestSerializer
    )
    def reschedule(self, request, *args, **kwargs):
        request_data = request.data
        request_data["requested_by"] = request.user.pk
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RescheduleRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.RescheduleRequestSerializer
    queryset = models.RescheduleRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['GET'],
        detail=False
    )
    def availability_slots(self, request, *args, **kwargs):
        now = datetime.datetime.now()
        start_date = now.date()
        num_days = 7
        date_list = [start_date + datetime.timedelta(days=day) for day in range(num_days)]
        weekday_timeslot_map = choices.RESCHEDULE_WEEKDAY_TIME_SLOT_MAP
        data = []
        for date in date_list:
            time_slots = []
            for slot in weekday_timeslot_map:
                timeslot = datetime.datetime.combine(date, slot)
                if timeslot > now:
                    time_slots.append(timeslot.isoformat())
            if len(time_slots) > 0:
                data.append(time_slots)
        return Response(data)
        
    @action(
        methods=['POST'],
        detail=False
    )
    def accepted(self, request, *args, **kwargs):
        request_data = request.data
        approver = request.user
        reschedule_request_id = request_data.get("reschedule_request")

        try:
            selected_time_slot = datetime.datetime.strptime(
                request_data["time_slot"],
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        except ValueError:
            return self.generate_bad_request(
                {"error": "Invalid datetime format."}
            )

        #TODO: Clean up this timezone stuff (Nishant) 
        selected_time_slot = selected_time_slot.astimezone(pytz.timezone(TIME_ZONE))
        selected_time_slot = selected_time_slot.astimezone(pytz.UTC)

        if not reschedule_request_id and selected_time_slot:
            return self.generate_bad_request(
                {"error": "Invalid request body. Missing id or time slots."}
            )

        try:
            reschedule_request = models.RescheduleRequest.objects.get(
                id=reschedule_request_id,
                approver=approver
            )
        except models.RescheduleRequest.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Reschedule request does not exist."}
            )

        if selected_time_slot not in reschedule_request.time_slots:
            return self.generate_bad_request(
                {"error": "Selected time slot is not a valid choice."}
            )

        reschedule_request.status = choices.RESCHEDULE_REQUEST_CONFIRMED
        reschedule_request.save()

        signals.reschedule_request_approved.send(
            sender=reschedule_request.__class__,
            reschedule_request=reschedule_request,
            time_slot=selected_time_slot
        )

        return Response({"success": True})

    @action(
        methods=['POST'],
        detail=False
    )
    def declined(self, request, *args, **kwargs):
        reschedule_request_id = request.data.get("id")
        approver = request.user
        
        if not reschedule_request_id:
            return self.generate_bad_request(
                {"error": "Invalid request body. Missing id or time slots."}
            )

        try:
            reschedule_request = models.RescheduleRequest.objects.get(
                id=reschedule_request_id,
                approver=approver
            )
        except models.RescheduleRequest.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Reschedule request does not exist."}
            )

        reschedule_request.status = choices.RESCHEDULE_REQUEST_DECLINED
        reschedule_request.save()

        signals.reschedule_request_declined.send(
            sender=reschedule_request.__class__,
            reschedule_request=reschedule_request,
        )

        return Response({"success": True})

    def retrieve(self, request, *args, **kwargs):

        meeting_id = kwargs.get('pk')
        if not meeting_id:
            return self.generate_bad_request({'error': 'Bad request'})
        try:
            reschedule_obj = models.RescheduleRequest.objects.get(
                old_meeting_id=meeting_id,
                approver=request.user,
            )
        except models.RescheduleRequest.DoesNotExist:
            return self.generate_bad_request({'error': 'Incorrect Meeting id'})
        except models.RescheduleRequest.MultipleObjectsReturned:
            return self.generate_bad_request({'error': 'Incorrect Meeting id'})
        serializer = self.get_serializer(reschedule_obj)
        return Response(serializer.data)
