import datetime
import json
import pytz

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status

from users import permissions
from resources.meetings import models
from resources.meetings import serializers
from resources.meetings import choices
from resources.meetings import receivers
from resources.meetings import services
from resources.meetings import signals
from cryptography.fernet import InvalidToken
from integrations.freshchat import constants


class MeetingConfigPublicViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.ConfigPublicSerializer
    queryset = models.Config.objects.all()
    permission_classes = [permissions.AllowAny]


class MeetingPreferencePublicViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.PublicMeetingPreferenceSerializer
    queryset = models.MeetingPreference.objects.all()
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["meeting", "user"]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["get"],
        serializer_class=serializers.PublicMeetingPreferenceSerializer,
        permission_classes=[permissions.AllowAny],
        detail=False
    )
    def latest(self, request, *args, **kwargs):
        """Get the latest preference for each user.

        Note:
            The user may have registered for a meeting multiple times,
            get the user"s latest preference.

        """

        # Create pk list for latest preference for all users and send
        # it as a query set.
        preference_pk_list = []
        for user in get_user_model().objects.all():
            preference = user.meeting_preferences.first()
            if not preference:
                continue
            preference_pk_list.append(preference.id)

        self.queryset = models.MeetingPreference.objects.filter(id__in=preference_pk_list)

        response = super(MeetingPreferencePublicViewSet, self).list(request, *args, **kwargs)
        return response

    @action(
        methods=["post"],
        serializer_class=serializers.PublicMeetingPreferenceSerializer,
        permission_classes=[permissions.AllowAny],
        detail=False
    )
    def optin(self, request, *args, **kwargs):
        """Check if the user has past user preferences and opt them for this week.

        Note:
            This is a public view which gets user from
                a encoded string in the body and creates
                a user meeting preference object for the
                user.

        """
        data = request.data.get("user")
        if not data:
            return self.generate_bad_request(
                {"error": "Query data missing"}
            )

        try:
            user = services.get_user_from_opt_in_url(data)
            old_preference = user.meeting_preferences.first()
            if not old_preference:
                return self.generate_bad_request({
                    "error": "If this is the first time you're opting in please use the app to indicate your preferences."
                })

            latest_meeting_config = services.get_latest_active_meeting_config()
            current_week_start_date = latest_meeting_config.week_start_date
            new_time_slots = []
            for time_slot in old_preference.time_slots.all():
                day = time_slot.date.weekday()
                date_diff = day - current_week_start_date.weekday()
                if date_diff < 0:
                    return self.generate_bad_request(
                        {"error": "Please check back at a later time."}
                    )

                new_date = current_week_start_date + datetime.timedelta(days=date_diff)
                time_slot, _ = models.TimeSlot.objects.get_or_create(
                    date=new_date,
                    start_time=time_slot.start_time,
                    end_time=time_slot.end_time
                )
                new_time_slots.append(time_slot)

            created = False
            new_meeting_preference = models.MeetingPreference.objects.filter(
                meeting=latest_meeting_config,
                user=user,
            ).first()

            if not new_meeting_preference:
                created = True
                new_meeting_preference = models.MeetingPreference.objects.create(
                    meeting=latest_meeting_config,
                    user=user,
                )

            if not created:
                return self.generate_bad_request(
                    {"error": "You have already signed up for the week. If you'd like to edit your preferences please use the app."}
                )

            for obj in old_preference.objectives.all():
                new_meeting_preference.objectives.add(obj)

            looking_for_objective = old_preference.objectives.filter(type=choices.OBJECTIVE_TYPES[0][0]).first()
            looking_to_objective = old_preference.objectives.filter(type=choices.OBJECTIVE_TYPES[1][0]).first()

            objectives_str = "{} & {}".format(looking_for_objective.name, looking_to_objective.name) \
                if (looking_for_objective and looking_to_objective) else constants.MEETING_REGISTRATION_DEFAULT_OBJECTIVE_TEXT

            for interest in old_preference.interests.all():
                new_meeting_preference.interests.add(interest)
        
            for slot in new_time_slots or []:
                new_meeting_preference.time_slots.add(slot)

            signals.new_meeting_registration.send(sender=new_meeting_preference.__class__, preference=new_meeting_preference)
            return Response(data={"objective": objectives_str})

        except InvalidToken:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )
        except get_user_model().DoesNotExist:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )


class MeetingPublicViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):

    serializer_class = serializers.PublicMeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["config"]

    def create(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            meeting_date = datetime.datetime.strptime(data["date"], "%d/%m/%Y")
            start_time = datetime.datetime.strptime(data["start_time"], "%H:%M").time()
            end_time = datetime.datetime.strptime(data["end_time"], "%H:%M").time()
            start = datetime.datetime.combine(meeting_date, start_time)
            end = datetime.datetime.combine(meeting_date, end_time)
        except ValueError:
            return Response(
                status=400,
                data={
                    "message": "Please input proper for date and time."
                }
            )
        if start_time > end_time:
            return Response(
                status=400,
                data={
                    "message": "Start time should be greater that end time."
                }
            )

        meeting_config = services.get_current_week_meeting_config()
        if not meeting_config:
            return Response(
                status=400,
                data={
                    "message": "No active meeting config is present."
                }
            )

        data = {
            "config": meeting_config.id,
            "participants": data["participants"],
            "start": start,
            "end": end
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        response = super(MeetingPublicViewSet, self).list(request, *args, **kwargs)
        final_response = []

        for data in response.data:
            response_dict = dict(data)
            participants_emails = get_user_model().objects.filter(
                    uuid__in=response_dict["participants"]
                ).values_list("email", flat=True)
            start = datetime.datetime.strptime(response_dict["start"], settings.DEFAULT_DATETIME_FORMAT)
            end = datetime.datetime.strptime(response_dict["end"], settings.DEFAULT_DATETIME_FORMAT)
            data = {
                "id": response_dict["pk"],
                "config": response_dict["config"],
                "participants": ", ".join(participants_emails),
                "meeting_date": start.date(),
                "start_time": start.time(),
                "end_time": end.time(),
                "meeting_link": response_dict["link"],
                "status": response_dict["status"],
            }
            final_response.append(data)

        return Response(final_response)

    def retrieve(self, request, *args, **kwargs):
        request_user_id = kwargs["pk"]
        response = super(MeetingPublicViewSet, self).list(request, *args, **kwargs)
        final_response = []

        for data in response.data:
            response_dict = dict(data)
            start = response_dict.get("start")
            if not start:
                continue
            start_datetime = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%fZ")

            end = response_dict.get("end")
            if not end:
                end = start + datetime.timedelta(minutes=30)
            end_datetime = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%fZ")

            meeting_link = response_dict.get("link")
            user = None
            participants = response_dict.get("participants")

            for participant in participants:
                if str(participant.get("pk")) == request_user_id:
                    continue
                user = get_user_model().objects.get(pk=participant.get("pk"))

            if not user:
                continue

            meeting_date = start_datetime.strftime("%Y-%m-%d")
            start_time = start_datetime.strftime("%H:%M")
            end_time = end_datetime.strftime("%H:%M")

            user_data = {
                "id": response_dict.get("pk"),
                "config": response_dict.get("config"),
                "email": user.email,
                "meeting_date": meeting_date,
                "start_time": start_time,
                "end_time": end_time,
                "meeting_link": meeting_link,
                "status": response_dict.get("status"),
            }
            final_response.append(user_data)

        return Response(final_response)


class MeetingCommunicationViewSet(
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.AllowAny]


class RescheduleRequestPublicViewSet( 
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.RescheduleRequestSerializer
    queryset = models.RescheduleRequest.objects.all()
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        data = request.query_params.get("reschedule")
        try:
            user, reschedule = services.get_reschedule_from_url(data)
            if reschedule.approver.pk != user.pk:
                return self.generate_bad_request({
                    "error": "You do not have permission to reschedule. Please contact WorkNetwork if you think this is a mistake."
                })

            if reschedule.status != choices.RESCHEDULE_REQUEST_PENDING_APPROVAL:
                return self.generate_bad_request({
                    "error": "You have already responded to this reschedule request."
                })

            return Response(data=self.get_serializer(reschedule).data)

        except InvalidToken:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )
        except models.RescheduleRequest.DoesNotExist:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )
        except get_user_model().DoesNotExist:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )

    @action(
        methods=["POST"],
        detail=False
    )
    def confirmed(self, request, *args, **kwargs):
        reschedule_request_id = request.data.get("id")
        try:
            # TODO(Nishant): Replace this with datetime.datetime.fromisoformat()
            selected_time_slot = datetime.datetime.strptime(
                request.data["time_slot"], 
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
        
        if not reschedule_request_id:
            return self.generate_bad_request(
                {"error": "Reschedule request does not exist. Please check the URL."}
            )

        try:
            reschedule_request = models.RescheduleRequest.objects.get(
                id=reschedule_request_id,
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
        

class MeetingRSVPPublicViewSet(
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingRSVPSerializer
    queryset = models.MeetingRSVP.objects.all()
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["POST"],
        detail=False,
    )
    def attending(self, request):
        """Check if the user is attending the meeting and mark it.

        Note:
            This is a public view which gets user and meeting id from
                a encoded string in the body and marks the user
                as attending for the meeting.

        """
        data = request.data.get("meeting")
        if not data:
            return self.generate_bad_request(
                {"error": "Query data missing"}
            )

        try:
            user, meeting = services.get_user_meeting_from_url(data)
            if meeting.status == choices.MEETING_STATUS_CANCELLED:
                return self.generate_bad_request({
                    "error": "This meeting has been cancelled. Please contact WorkNetwork if you think this is a mistake."
                })
            if meeting.status == choices.MEETING_STATUS_RESCHEDULED:
                return self.generate_bad_request({
                    "error": "This meeting has been rescheduled or a reschedule request is pending. Please contact WorkNetwork if you think this is a mistake."
                })
            rsvp = models.MeetingRSVP.objects.get(
                meeting=meeting,
                participant=user,
            )
            if rsvp.status == choices.MEETING_RSVP_STATUS_CHOICES[0][0]:
                return self.generate_bad_request({
                    "error": "You have already RSVPed for this meeting."
                })
            rsvp.status = choices.MEETING_RSVP_STATUS_CHOICES[0][0]
            rsvp.save()

            # Send a signal which updates the status after RSVP is
            # updated.
            signals.rsvp_status_updated.send(
                sender=rsvp.__class__,
                user=user,
                rsvp=rsvp
            )
            return Response(data={"start": meeting.start})

        except InvalidToken:
            return self.generate_bad_request(
                {"error": "Please check the URL and try again."}
            )
        except models.get_user_model().DoesNotExist:
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
