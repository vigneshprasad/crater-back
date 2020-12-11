import datetime
import json

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets

from users import permissions
from resources.meetings import models, choices
from resources.meetings import serializers
from resources.meetings import services



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

    def list(self, request, *args, **kwargs):
        response = super(MeetingPreferencePublicViewSet, self).list(request, *args, **kwargs)
        final_response = []
        for data in response.data:
            response_dict = dict(data)
            user = get_user_model().objects.get(
                uuid=response_dict["user"]
            )
            try:
                objectives = models.Objective.objects.filter(
                    id__in=response_dict["objectives"]
                ) if response_dict["objectives"] else None
            except models.Objective.DoesNotExist:
                objectives = None

            looking_for_objectives = objectives.filter(type=choices.OBJECTIVE_TYPES[0]) if objectives else ""
            looking_to_objectives = objectives.filter(type=choices.OBJECTIVE_TYPES[1]) if objectives else ""

            interests = models.Interest.objects.filter(
                id__in=response_dict["interests"]
            )
            interests_names = ', '.join([interest.name for interest in interests])

            time_slots = models.TimeSlot.objects.filter(
                id__in=response_dict["time_slots"]
            )
            time_slots_display = ',\n'.join([time_slot.get_display() for time_slot in time_slots])
            new_data = {
                "pk": response_dict["pk"],
                "uuid": user.uuid,
                "email": user.email,
                "looking_for": [looking_for.name for looking_for in looking_for_objectives],
                "looking_to": [looking_to.name for looking_to in looking_to_objectives],
                "interests": interests_names,
                "time_slots": time_slots_display
            }
            final_response.append(new_data)

        return Response(final_response)


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

        meeting_config = services.get_latest_active_meeting_config()
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
