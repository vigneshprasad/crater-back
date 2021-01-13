import datetime
import json
import pytz

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
from freelance.settings import TIME_ZONE

from users import permissions
from resources.meetings import models
from resources.meetings import serializers
from resources.meetings import choices
from resources.meetings import services
from resources.meetings import signals
from cryptography.fernet import InvalidToken


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
    filterset_fields = ['meeting', 'user']

    @action(
        methods=['get'],
        serializer_class=serializers.PublicMeetingPreferenceSerializer,
        permission_classes=[permissions.AllowAny],
        detail=False
    )
    def latest(self, request, *args, **kwargs):
        """Get the latest preference for each user.

        Note:
            The user may have registered for a meeting multiple times,
            get the user's latest preference.

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


class MeetingPublicViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):

    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['config']

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

        time_slot, _ = models.MeetingTimeSlot.objects.get_or_create(
            date=meeting_date,
            start_time=start_time,
            end_time=end_time
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
            "time_slot": time_slot.id,
            "start": start,
            "end": end,
            "is_canceled": data.get("is_canceled", False)
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
                ).values_list('email', flat=True)
            time_slot = models.MeetingTimeSlot.objects.get(id=response_dict["time_slot"])
            date = time_slot.date
            start_time = time_slot.start_time
            end_time = time_slot.end_time
            data = {
                "id": response_dict["pk"],
                "config": response_dict["meeting_config"],
                "participants": ", ".join(participants_emails),
                "meeting_date": date,
                "start_time": start_time,
                "end_time": end_time,
                "meeting_link": response_dict["link"],
                "status": response_dict["status"],
                "canceled": response_dict["is_canceled"]
            }
            final_response.append(data)

        return Response(final_response)

    def retrieve(self, request, *args, **kwargs):
        request_user_id = kwargs['pk']
        response = super(MeetingPublicViewSet, self).list(request, *args, **kwargs)
        final_response = []

        for data in response.data:
            response_dict = dict(data)
            start = response_dict.get('start')
            if not start:
                continue
            start_datetime = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%fZ")

            end = response_dict.get('end')
            if not end:
                end = start + datetime.timedelta(minutes=30)
            end_datetime = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%fZ")

            meeting_link = response_dict.get('link')
            user = None
            participants = response_dict.get('participants')

            for participant in participants:
                if str(participant.get('pk')) == request_user_id:
                    continue
                user = get_user_model().objects.get(pk=participant.get('pk'))

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
                "canceled": response_dict.get("is_canceled")
            }
            final_response.append(user_data)

        return Response(final_response)


class MeetingCommunicationViewSet(
    viewsets.GenericViewSet
):
    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.AllowAny]

    # @action(
    #     methods=['get', 'post'],
    #     serializer_class=serializers.MeetingSerializer,
    #     permission_classes=[permissions.AllowAny],
    #     detail=False
    # )
    # # TODO(Nishant): Take list of meeting ids to send emails to a subset of meetings.
    # def send_intro_emails(self, request, *args, **kwargs):
    #     if request.method == 'GET':
    #         all_active_meetings = services.get_active_meetings()
    #         all_data = []
    #         for active_meeting in all_active_meetings:
    #             if not active_meeting.participants.count() == choices.MAX_MEMBER_FOR_ONE_ON_ONE:
    #                 continue
    #
    #             p1 = active_meeting.participants.all()[0]
    #             p2 = active_meeting.participants.all()[1]
    #
    #             # Checking if profile exists.
    #             if not (p1.has_profile and p2.has_profile):
    #                 continue
    #
    #             display_day = active_meeting.time_slot.get_display_day()
    #             display_time = active_meeting.time_slot.get_display_time()
    #
    #             subject = 'Introducing {} & {}'.format(
    #                 p1.name.title(),
    #                 p2.name.title()
    #             )
    #             data = {
    #                 'meeting_id': active_meeting.id,
    #                 'day': display_day,
    #                 'time': display_time,
    #                 'name_a': p1.name.title(),
    #                 'name_b': p2.name.title(),
    #                 'link': active_meeting.link,
    #                 'introduction_a': p1.profile.get_introduction(),
    #                 'introduction_b': p2.profile.get_introduction(),
    #                 'linkedin_a': p1.profile.linkedin_url,
    #                 'linkedin_b': p2.profile.linkedin_url,
    #             }
    #             all_data.append(data)
    #         return Response(all_data)
    #
    #     if request.method == 'POST':
    #         tasks.send_1_on_1_meeting_intro_emails()
    #
    #     return Response({'status': 'SUCCESS'})


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
                    'error': 'You do not have permission to reschedule. Please contact WorkNetwork if you think this is a mistake.'
                })

            if reschedule.status != choices.RESCHEDULE_REQUEST_PENDING_APPROVAL:
                return self.generate_bad_request({
                    'error': 'You have already responded to this reschedule request.'
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
        methods=['POST'],
        detail=False
    )
    def confirmed(self, request, *args, **kwargs):
        reschedule_request_id = request.data.get("id")
        try:
            selected_time_slot = datetime.datetime.strptime(
                request.data["time_slot"], 
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            
        except ValueError:
            return self.generate_bad_request(
                {"error": "Invalid datetime format."}
            )

        # TODO(Nishant): Clean up this timezone stuff.
        selected_time_slot = selected_time_slot.astimezone(pytz.timezone(TIME_ZONE))
        selected_time_slot = selected_time_slot.astimezone(pytz.UTC)

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