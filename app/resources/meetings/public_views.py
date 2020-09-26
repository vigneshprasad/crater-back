import datetime
import json

from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import mixins, viewsets

from users import permissions
from resources.meetings import models
from resources.meetings import serializers
from resources.meetings import services


class UserMeetingPreferencePublicViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.UserMeetingPreferenceSerializer
    queryset = models.UserMeetingPreference.objects.all()
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['meeting']

    def list(self, request, *args, **kwargs):
        response = super(UserMeetingPreferencePublicViewSet, self).list(request, *args, **kwargs)
        final_response = []
        for data in response.data:
            response_dict = dict(data)
            user = get_user_model().objects.get(
                uuid=response_dict["user"]
            )
            try:
                objectives = models.Objective.objects.get(
                    id=response_dict["objectives"]
                ).name if response_dict["objective"] else None
            except models.Objective.DoesNotExist:
                objectives = None

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
                "number_of_meetings": response_dict["number_of_meetings"],
                "objective": response_dict["objective"],
                "new_objective": objectives,
                "interests": interests_names,
                "time_slots": time_slots_display
            }
            final_response.append(new_data)

        return Response(final_response)


class MeetingViewSetPublicViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):

    serializer_class = serializers.MeetingSerializer
    queryset = models.Meeting.objects.all()
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['meeting_config']

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
        data = {
            "meeting_config": meeting_config.id,
            "participants": data["participants"],
            "time_slot": time_slot.id,
            "link": data["meeting_link"],
            "start": start,
            "end": end,
            "is_canceled": data.get("is_canceled", False)
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        self.perform_create(serializer)

        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        response = super(MeetingViewSetPublicViewSet, self).list(request, *args, **kwargs)
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
                "meeting_config": response_dict["meeting_config"],
                "participants": ", ".join(participants_emails),
                "meeting_link": response_dict["link"],
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "canceled": response_dict["is_canceled"]
            }
            final_response.append(data)

        return Response(final_response)

    @action(
        methods=['patch'],
        serializer_class=serializers.MeetingSerializer,
        permission_classes=[permissions.AllowAny],
        detail=False
    )
    def batch_update(self, request):
        queryset = self.get_queryset()
        print(request.body)
        data = json.loads(request.body)["bulk_update_data"]
        meeting_ids = [d["id"] for d in data]
        print(data)
        for update_data in data:
            queryset = queryset.filter(id__in=meeting_ids).update(**update_data)
        return Response([])
