import datetime

import pytz
from django.db.models import Prefetch, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from freelance.settings import DEFAULT_DATETIME_FORMAT
from resources.meetings import choices, models, receivers, serializers, services, signals
from resources.meetings.models import Meeting
from users import models as user_models, paginators as user_paginators, permissions as user_permissions, \
    serializers as user_serializers


class MeetingConfigViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingConfigSerializer
    queryset = models.Config.objects.all()
    permission_classes = [user_permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        instance = services.get_latest_active_meeting_config()
        # If there is no active meeting with registration open
        # return and empty response.
        if not instance:
            return Response({})

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class UserMeetingPreferenceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.UserMeetingPreferenceSerializer
    queryset = models.MeetingPreference.objects.all()
    permission_classes = [user_permissions.IsAuthenticated]

    @action(
        methods=["GET"],
        detail=False,
    )
    def past(self, request):
        user = request.user
        instance = models.MeetingPreference.objects.filter(user=user).last()
        if not instance:
            return Response(status=status.HTTP_204_NO_CONTENT)
        config = services.get_latest_active_meeting_config()
        slot_start_times = list(instance.time_slots.all().values_list("start_time", flat=True).distinct())
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
            return Response(status=status.HTTP_204_NO_CONTENT)

        instance = active_meeting.user_preferences.filter(user=user).last()
        if not instance:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serialized = self.get_serializer(instance)
        return Response(serialized.data)

    def _add_objectives_to_request(self):
        request = self.request
        objective = request.data.get("objective")

        if not objective:
            return request

        for choice in choices.OBJECTIVE_CHOICES:
            if choice[0] != objective:
                continue
            try:
                # TODO(Nishant): Check if we have to create a list of all objectives
                # or only one objective.
                objective_model = models.Objective.objects.get(name=choice[1], is_active=True)
                request.data["objectives"] = [objective_model.pk]
            except models.Objective.DoesNotExist:
                continue

        return request

    def update(self, request, *args, **kwargs):
        request = self._add_objectives_to_request()
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        response_serializer = serializers.UserMeetingPreferenceSerializer(instance)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If "prefetch_related" has been applied to a queryset, we need to
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
        if self.action == "create" or self.action == "update":
            return serializers.PostUserMeetingPreferenceSerializer
        else:
            return serializers.UserMeetingPreferenceSerializer


class MeetingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [user_permissions.IsAuthenticated]
    filterset_fields = ["participants"]

    def get_queryset(self):
        return self.request.user.meeting_set.all()

    def _get_meeting_queryset(self, is_past):
        now = timezone.now()
        f = Q(start__lte=now) if is_past else Q(start__gte=now)
        queryset = self.get_queryset().filter(f)
        return queryset

    def _create_data_by_date(self, queryset, reverse=False):
        f = Q(user_id=self.request.user.pk) if self.request.user else Q()
        participants = Prefetch(
            "participants",
            Meeting.participants.through.objects
            .exclude(f)
            .prefetch_related("meeting_rsvps")
        )
        data = self.get_serializer(
            queryset
            .select_related("config")
            .prefetch_related(participants),
            many=True
        ).data
        dates = {}
        for meeting in data:
            date = datetime.datetime.strptime(meeting["start"], DEFAULT_DATETIME_FORMAT).date()
            if date not in dates:
                dates[date] = {"date": date, "meetings": []}
            dates[date]["meetings"].append(meeting)
        return sorted(dates.values(), key=lambda x: x["date"], reverse=reverse)

    @action(
        methods=["GET"],
        detail=False,
    )
    def upcoming(self, request):
        queryset = self._get_meeting_queryset(is_past=False)
        data = self._create_data_by_date(queryset=queryset)
        return Response(data)

    @action(
        methods=["GET"],
        detail=False,
    )
    def past(self, request):
        queryset = self._get_meeting_queryset(is_past=True)
        data = self._create_data_by_date(queryset=queryset, reverse=True)
        return Response(data)


class MeetingObjectivesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.MeetingObjectiveSerializer
    queryset = models.Objective.objects.filter(is_active=True)
    permission_classes = [user_permissions.IsAuthenticated]


class MeetingInterestsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.MeetingInterestSerializer
    queryset = models.Interest.objects.filter(is_active=True)
    permission_classes = [user_permissions.IsAuthenticated]


class MeetingConfigV2ViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.MeetingConfigV2Serializer
    queryset = models.Config.objects.all()
    permission_classes = [user_permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        instance = services.get_latest_active_meeting_config()
        if not instance:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serialized = self.get_serializer(instance)
        return Response(serialized.data)


class MeetingRSVPViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingRSVPSerializer
    queryset = models.MeetingRSVP.objects.all()
    permission_classes = [user_permissions.IsAuthenticated]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["POST"],
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
        methods=["POST"],
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
        methods=["POST"],
        detail=False,
        serializer_class=serializers.PostRescheduleRequestSerializer
    )
    def reschedule(self, request, *args, **kwargs):
        request_data = request.data
        request_data["requested_by"] = request.user.pk
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        signals.reschedule_request_created.send(
            sender=instance.__class__,
            reschedule_request=instance
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RescheduleRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.RescheduleRequestSerializer
    queryset = models.RescheduleRequest.objects.all()
    permission_classes = [user_permissions.IsAuthenticated]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["GET"],
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
        methods=["POST"],
        detail=False
    )
    def accepted(self, request, *args, **kwargs):
        request_data = request.data
        approver = request.user
        reschedule_request_id = request_data.get("reschedule_request")

        try:
            # TODO(Nishant): Replace this with datetime.datetime.fromisoformat()
            selected_time_slot = datetime.datetime.strptime(
                request_data["time_slot"],
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        except ValueError:
            return self.generate_bad_request(
                {"error": "Invalid datetime format."}
            )
        selected_time_slot = selected_time_slot.replace(tzinfo=pytz.UTC)

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

        if reschedule_request.status != choices.RESCHEDULE_REQUEST_PENDING_APPROVAL:
            return self.generate_bad_request(
                {"error": "You have already responded to the reschedule request."}
            )

        if selected_time_slot not in reschedule_request.time_slots:
            return self.generate_bad_request(
                {"error": "Selected time slot is not a valid choice."}
            )

        receivers.create_new_meeting_on_reschedule_request_approval(
            reschedule_request=reschedule_request,
            time_slot=selected_time_slot
        )

        # This signal is fired once reschedule request is accepted and
        # new meeting is created for the same.
        signals.reschedule_request_approved.send(
            sender=reschedule_request.__class__,
            reschedule_request=reschedule_request
        )

        return Response({"success": True})

    @action(
        methods=["POST"],
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

        meeting_id = kwargs.get("pk")
        if not meeting_id:
            return self.generate_bad_request({"error": "Bad request"})
        try:
            reschedule_obj = models.RescheduleRequest.objects.get(
                old_meeting_id=meeting_id,
                approver=request.user,
            )
        except models.RescheduleRequest.DoesNotExist:
            return self.generate_bad_request({"error": "Incorrect Meeting id"})
        except models.RescheduleRequest.MultipleObjectsReturned:
            return self.generate_bad_request({"error": "Incorrect Meeting id"})
        serializer = self.get_serializer(reschedule_obj)
        return Response(serializer.data)


class MeetingRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingRequestSerializer
    queryset = models.MeetingRequest.objects.filter(is_expired=False)
    permission_classes = [user_permissions.IsAuthenticated]
    filterset_fields = []

    def _create_data_by_date(self, queryset):
        """Returns meeting requests per date for a given queryset."""
        response = []
        dates = list(queryset.values_list("expires_at__date", flat=True).distinct())
        # Reverse date list from start to end.
        dates.reverse()

        for date in dates:
            if not date:
                continue
            meeting_requests = queryset.filter(expires_at__date=date)
            serialized = self.get_serializer(meeting_requests, many=True)
            response.append({
                "date": date.isoformat(),
                "meeting_requests": serialized.data,
            })

        return response

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["GET"],
        detail=False,
        queryset=user_models.Profile.objects.filter(allow_meeting_request=True),
        serializer_class=user_serializers.ProfileSerializer,
        pagination_class=user_paginators.Pagination,
    )
    def users(self, request, *args, **kwargs):
        """Returns serialized list of users the requesting user
            can send meeting request to.

        """
        user = request.user
        queryset = self.filter_queryset(self.get_queryset()).exclude(user=user)
        results = queryset.filter(user__score__lte=user.score).order_by("-user__score")
        page = self.paginate_queryset(results)

        if page is None:
            serialized = self.get_serializer(results, many=True)
            return Response(serialized.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["GET"],
        detail=False
    )
    def slots(self, request, *args, **kwargs):
        """Returns available slots for setting up a meeting request."""
        now_datetime = datetime.datetime.now()
        start_date = now_datetime.date()
        num_days = 7
        date_list = [start_date + datetime.timedelta(days=day) for day in range(num_days)]
        weekday_timeslot_map = choices.MEETING_REQUEST_SLOTS
        data = []

        for date in date_list:
            time_slots = []
            for slot in weekday_timeslot_map:
                timeslot = datetime.datetime.combine(date, slot)
                if timeslot <= now_datetime:
                    continue
                time_slots.append(timeslot.isoformat())

            if not len(time_slots):
                continue
            data.append(time_slots)

        return Response(data)

    @action(
        methods=["POST"],
        detail=False
    )
    def accepted(self, request, *args, **kwargs):
        request_data = request.data
        meeting_request_id = request_data.get("meeting_request")
        selected_time_slot_str = request_data.get("time_slot")

        try:
            meeting_request = self.get_queryset().get(id=meeting_request_id)
        except models.MeetingRequest.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Meeting request does not exist."}
            )

        try:
            # TODO(Nishant): Replace this with datetime.datetime.fromisoformat()
            selected_time_slot = datetime.datetime.strptime(
                selected_time_slot_str,
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        except ValueError:
            return self.generate_bad_request(
                {"error": "Invalid datetime format."}
            )
        selected_time_slot = selected_time_slot.replace(tzinfo=pytz.UTC)

        data = {
            "selected_time_slot": selected_time_slot,
            "status": choices.MEETING_REQUEST_CONFIRMED
        }
        serializer = self.get_serializer(meeting_request, data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Fire a signal notifying meeting request is approved.
        signals.meeting_request_approved.send(
            sender=meeting_request.__class__,
            meeting_request=meeting_request
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["POST"],
        detail=False
    )
    def declined(self, request, *args, **kwargs):
        meeting_request_id = request.data.get("meeting_request")
        try:
            meeting_request = self.get_queryset().get(id=meeting_request_id)
        except models.MeetingRequest.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Meeting request does not exist."}
            )

        data = {
            "status": choices.MEETING_REQUEST_DECLINED
        }
        serializer = self.get_serializer(meeting_request, data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Send a signal notifying meeting request is declined.
        signals.meeting_request_declined.send(
            sender=meeting_request.__class__,
            meeting_request=meeting_request,
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["GET"],
        detail=False,
        filterset_fields=["status"]
    )
    def my(self, request, *args, **kwargs):
        """Returns users meeting request, both to and by."""

        user = request.user
        # Get the filtered queryset.
        meeting_requests = self.filter_queryset(self.get_queryset())

        # Get meetings request for user, both requested to and requested by.
        user_meeting_requests = meeting_requests.filter(
            Q(requested_by=user) | Q(requested_to=user)
        )
        response_data = self._create_data_by_date(queryset=user_meeting_requests)

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )
