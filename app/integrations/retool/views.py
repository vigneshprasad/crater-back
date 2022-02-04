import datetime

from dateutil import relativedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import mixins, viewsets

from users import permissions
from conversations import constants as conversations_constants
from conversations import models as conversations_models
from integrations.dyte import models as dyte_models


DATE_JOINED_DURATION_CHOICES = [
    24,
    7*24,
    14*24,
    30*24
]

# Default start date in case not provided.
DEFAULT_START_DATE = datetime.datetime(2021, 1, 1)
# Start of streams (We are treating this as global start date for all metrics)
GLOBAL_START = datetime.datetime(2021, 10, 1)
# Start date to calculate Weekly active users.
GLOBAL_WAU_START = datetime.datetime(2021, 10, 4)

# Email to exclude for data.
EMAIL_TO_EXCLUDE = [
    "vignesh@worknetwork.in",
    "abhishek@worknetwork.in",
    "nishant@worknetwork.in",
    "vivan@worknetwork.in",
    "vivan@crater.club",
    "ram@worknetwork.in",
    "sujith@crater.club",
    "shivanivijay2796@gmail.com",
    "shivaniv27@yahoo.co.in",
    "rjtnndn@gmail.com",
    "sanjeevraichur29@gmail.com"
]


class RetoolDataViewSet(
    viewsets.GenericViewSet
):
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["get"],
        detail=False,
    )
    def rsvp_by_duration(self, request, *args, **kwargs):
        """Get RSVP after user date joined.

        Data Points:
            RSVP after 24 hours (D1).
            RSVP/Online after a week (D7).
            RSVP/Online after 14 days (D14).
            RSVP/Online after 30 days (D30).

        """

        duration = int(request.query_params.get("duration", 24))
        start_date = DEFAULT_START_DATE
        end_date = timezone.now()

        rsvp_after_date_joined_duration = []

        all_rsvps = conversations_models.Request.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by("created_at").values(
            "requester_id",
            "requester__date_joined",
            "created_at"
        )

        for rsvp in all_rsvps:
            if (rsvp["requester__date_joined"] + datetime.timedelta(hours=duration)) > rsvp["created_at"]:
                continue
            if rsvp["requester_id"] in rsvp_after_date_joined_duration:
                continue
            rsvp_after_date_joined_duration.append(rsvp["requester_id"])

        return Response(len(rsvp_after_date_joined_duration), status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def streams_by_duration(self, request, *args, **kwargs):
        """Get stream performed by speakers after duration.

        Data points:
            Stream after 24 hours
            Stream after a week
            Stream after 14 days
            Stream after 30 days

        """
        duration = int(request.query_params.get("duration", 24))
        start_date = DEFAULT_START_DATE
        end_date = timezone.now()

        number_of_streams_after_duration = []

        speakers = conversations_models.Group.objects.filter(
            start__gte=start_date,
            start__lte=end_date,
            type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM
        ).values_list("speakers", flat=True)

        for speaker in speakers:
            groups = conversations_models.Group.objects.filter(
                speakers=speaker,
                start__gte=start_date,
                start__lte=end_date
            ).order_by("start")
            if groups.count() <= 1:
                continue

            if speaker in number_of_streams_after_duration:
                continue

            first_stream = groups.first()
            last_stream = groups.last()
            if last_stream.start - first_stream.start > timezone.timedelta(hours=duration):
                number_of_streams_after_duration.append(speaker)

        return Response(len(number_of_streams_after_duration), status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def dau(self, request, *args, **kwargs):
        """Daily active users.

        Data Point:
            DAU

        """

        start_date = GLOBAL_START
        start_datetime = start_date.date()
        end_date = timezone.now()
        end_datetime = end_date.date()

        # Recalculate start datetime based on GLOBAL_START.
        start_datetime = start_datetime if start_datetime > GLOBAL_START.date() else GLOBAL_START.date()

        time_spent = end_datetime - start_datetime
        days = time_spent.days

        all_rsvps = 0
        start = start_datetime

        for i in range(0, days):
            end = start + timezone.timedelta(days=1)
            unique_rsvps = conversations_models.Request.objects.filter(
                created_at__gte=start,
                created_at__lte=end
            ).values("requester_id").distinct()

            all_rsvps += unique_rsvps.count()
            start += timezone.timedelta(days=1)

        return Response(round(all_rsvps / days, 2), status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def wau(self, request):
        """Weekly active users.

        Data Points:
            WAU

        """
        start_date = GLOBAL_WAU_START
        start_datetime = start_date.date()

        end_date = timezone.now()
        end_datetime = end_date.date()

        # Recalculate start datetime based on GLOBAL_START.
        start_datetime = start_datetime if start_datetime > GLOBAL_WAU_START.date() else GLOBAL_WAU_START.date()

        time_spent = end_datetime - start_datetime
        days = time_spent.days
        weeks = int(days / 7)

        all_rsvps = 0
        start = start_datetime

        for i in range(0, weeks):
            end = start + timezone.timedelta(days=7)
            unique_rsvps = conversations_models.Request.objects.filter(
                created_at__gte=start,
                created_at__lte=end
            ).values("requester_id").distinct()

            all_rsvps += unique_rsvps.count()
            start += timezone.timedelta(days=7)

        return Response(round(all_rsvps / weeks, 2), status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def mau(self, request):
        """Monthly active users.

        Data Point:
            MAU

        """
        start_date = GLOBAL_START
        start_datetime = start_date.date()

        end_date = timezone.now()
        end_datetime = end_date.date()

        # Recalculate start datetime based on GLOBAL_START.
        start_datetime = start_datetime if start_datetime > GLOBAL_START.date() else GLOBAL_START.date()

        r = relativedelta.relativedelta(end_datetime, start_datetime)
        # Get month difference between the start and end.
        months = (r.years * 12) + r.months or 1

        all_rsvps = 0
        start = start_datetime

        for i in range(0, months):
            end = start + relativedelta.relativedelta(months=1)
            unique_rsvps = conversations_models.Request.objects.filter(
                created_at__gte=start,
                created_at__lte=end
            ).values("requester_id").distinct()

            all_rsvps += unique_rsvps.count()
            start += relativedelta.relativedelta(months=1)

        return Response(round(all_rsvps / months, 2), status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def time_spent_by_user(self, request, *args, **kwargs):
        """Gets total and average minutes spent on streams for participants.

        Data Point:
            Avg. Time Per Viewer.
            Time spent by users

        """

        start_date = DEFAULT_START_DATE
        end_date = timezone.now()

        groups = conversations_models.Group.objects.filter(
            start__gte=start_date,
            start__lte=end_date,
            type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM
        )

        total_minutes = 0
        total_participants = 0
        total_stream_time = 0

        for group in groups:
            total_time_for_stream, avg_time_for_stream, participants_joined = _get_minutes_spent_by_participants_on_stream(
                group
                )
            if not avg_time_for_stream:
                continue

            total_minutes += avg_time_for_stream
            total_stream_time += total_time_for_stream
            total_participants += participants_joined

        avg_time_spent = (total_stream_time / total_participants) if total_participants else 0
        data = {
            "total_stream_time": total_stream_time,
            "total_participants": total_participants,
            "avg_time_spent": round(avg_time_spent, 2)
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def time_spent_by_streamers(self, request, *args, **kwargs):
        """Gets total and average minutes spent on streams for hosts.

        Data Point:
            Avg. Time Per Streamer
            Time spent by streamers

        """

        start_date = DEFAULT_START_DATE
        end_date = timezone.now()

        groups = conversations_models.Group.objects.filter(
            start__gte=start_date,
            start__lte=end_date,
            type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM
        )

        total_minutes = 0
        total_speakers = 0
        total_stream_time = 0

        for group in groups:
            total_time_for_stream, avg_time_for_stream, speakers_joined = _get_minutes_spent_by_hosts_on_stream(group)
            if not avg_time_for_stream:
                continue

            total_minutes += avg_time_for_stream
            total_stream_time += total_time_for_stream
            total_speakers += speakers_joined

        avg_time_spent = (total_stream_time / total_speakers) if total_speakers else 0
        data = {
            "total_stream_time": total_stream_time,
            "total_speakers": total_speakers,
            "avg_time_spent": round(avg_time_spent, 2)
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def avg_streams_per_month(self, request, *args, **kwargs):
        """Gets average sessions streamed per month by speakers.

        Data Point:
            Avg. sessions streamed per month (streamer)

        """

        start_date = GLOBAL_START
        end_date = timezone.now()

        end_datetime = end_date.date()

        all_speakers = conversations_models.Group.objects.filter(
            start__gte=start_date,
            start__lte=end_date
        ).values_list("speakers", flat=True)
        # Make speakers distinct.
        all_speakers = list(set(all_speakers))

        total_speakers = 0
        total_groups_streamed = 0
        total_groups_streamed_monthly = 0

        for speaker in all_speakers:
            try:
                user = get_user_model().objects.get(pk=speaker)
            except get_user_model().DoesNotExist:
                continue

            # Total groups attended.
            groups = conversations_models.Group.objects.filter(
                type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
                speakers=speaker,
                start__gte=start_date,
                start__lte=end_date
            ).count()

            # Either october or user date joined.
            global_start = user.date_joined.date() if user.date_joined.date() > GLOBAL_START.date() else GLOBAL_START.date()
            r = relativedelta.relativedelta(end_datetime, global_start)
            # Get month difference between the start and end.
            months_difference = (r.years * 12) + r.months

            if not groups:
                continue

            total_speakers += 1
            total_groups_streamed += groups
            total_groups_streamed_monthly += groups / months_difference if months_difference else groups

        return Response(round(total_groups_streamed_monthly / total_speakers, 2), status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def avg_views_per_month(self, request, *args, **kwargs):
        """Gets average sessions viewed per month by participants.

        Data Point:
            Avg. sessions viewed per month (user)

        """

        start_date = GLOBAL_START
        start_datetime = start_date.date()

        end_date = timezone.now()
        end_datetime = end_date.date()

        all_attendees = conversations_models.Group.objects.filter(
            start__gte=start_date,
            start__lte=end_date
        ).values_list("attendees", flat=True)
        # Make attendees distinct.
        all_attendees = list(set(all_attendees))

        total_attendees = 0
        total_groups_attended_monthly = 0

        for attendee in all_attendees:
            try:
                user = get_user_model().objects.get(pk=attendee)
            except get_user_model().DoesNotExist:
                continue

            groups = conversations_models.Group.objects.filter(
                type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
                attendees=attendee,
                start__gte=start_date,
                start__lte=end_date
            )
            attended_groups = 0
            for group in groups:
                dyte_meetings_attended = dyte_models.DyteMeetingParticipant.objects.filter(
                    participant_id=attendee,
                    dyte_meeting__group=group,
                    last_online_at__isnull=False
                )
                if dyte_meetings_attended:
                    attended_groups += 1

            start = user.date_joined.date() if user.date_joined.date() > GLOBAL_START.date() else GLOBAL_START.date()
            r = relativedelta.relativedelta(end_datetime, start)
            # Get month difference between the start and end.
            months_difference = (r.years * 12) + r.months

            total_attendees += 1
            total_groups_attended_monthly += attended_groups / months_difference if months_difference else attended_groups

        return Response(round(total_groups_attended_monthly / total_attendees, 2), status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
    )
    def avg_rsvps_per_month(self, request, *args, **kwargs):
        """Get average RSVP for stream per month.

        Data Point:
            Avg. sessions RSVPed per month (user)

        """

        start_date = GLOBAL_START
        start_datetime = start_date.date()

        end_date = timezone.now()
        end_datetime = end_date.date()

        all_attendees = conversations_models.Group.objects.filter(
            start__gte=start_date,
            start__lte=end_date
        ).values_list("attendees", flat=True)
        # Make attendees distinct.
        all_attendees = list(set(all_attendees))

        total_attendees = 0
        total_groups_attended_monthly = 0

        for attendee in all_attendees:
            try:
                user = get_user_model().objects.get(pk=attendee)
            except get_user_model().DoesNotExist:
                continue

            # Total groups attended.
            groups = conversations_models.Group.objects.filter(
                type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
                attendees=attendee,
                start__gte=start_date,
                start__lte=end_date
            ).count()

            # Either october or user date joined.
            global_start = user.date_joined.date() if user.date_joined.date() > GLOBAL_START.date() else GLOBAL_START.date()
            r = relativedelta.relativedelta(end_datetime, global_start)
            # Get month difference between the start and end.
            months_difference = (r.years * 12) + r.months

            if not groups:
                continue

            total_attendees += 1
            total_groups_attended_monthly += groups / months_difference if months_difference else groups

        return Response(round(total_groups_attended_monthly / total_attendees, 2), status=status.HTTP_200_OK)


# -------- PRIVATE FUNCTIONS -------- #
def _get_minutes_spent_by_participants_on_stream(group):

    speakers = group.speakers.values_list("pk", flat=True)
    participants = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group_id=group.id
    ).exclude(participant_id__in=speakers)

    total_minutes = 0
    participants_joined = 0

    for participant in participants:
        # If the participant never joined the call, return.
        if not participant.last_online_at:
            continue

        # If the participant joined the call before call start.
        if participant.last_online_at < group.start:
            continue

        # Get total time spent on the call.
        time_spent = participant.last_online_at - group.start
        minutes = time_spent.seconds // 60 % 60

        # If the time spent in 0 minutes, return.
        if not minutes and minutes > 300:
            continue

        participants_joined += 1
        total_minutes += minutes

    avg_time_spent = (total_minutes/participants_joined) if participants_joined else 0
    return total_minutes, round(avg_time_spent, 2), participants_joined


# ----------- PRIVATE FUNCTIONS ----------- #
def _get_minutes_spent_by_hosts_on_stream(group):

    speaker_ids = group.speakers.values_list("pk", flat=True)
    speakers = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group_id=group.id,
        participant_id__in=speaker_ids
    )

    total_minutes = 0
    speakers_joined = 0

    for speaker in speakers:
        # If the speaker never joined the call, return.
        if not speaker.last_online_at:
            continue

        # If the speaker joined the call before call start.
        if speaker.last_online_at < group.start:
            continue

        # Get total time spent on the call.
        time_spent = speaker.last_online_at - group.start
        minutes = time_spent.seconds // 60 % 60

        # If the time spent in 0 minutes, return.
        if not minutes and minutes > 300:
            continue

        speakers_joined += 1
        total_minutes += minutes

    avg_time_spent = (total_minutes/speakers_joined) if speakers_joined else 0
    return total_minutes, round(avg_time_spent, 2), speakers_joined
