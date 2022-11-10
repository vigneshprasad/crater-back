import datetime
import json
import logging
from itertools import chain

import boto3
from botocore import exceptions as botocore_exceptions
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from rest_framework.renderers import JSONRenderer

from communications.notifications import public as notifications_public
from conversations import constants, models, serializers, services, signals
from crater.creator import public as creator_public
from integrations.dyte import constants as dyte_constants, models as dyte_models, public as dyte_public
from integrations.firebase import private as firebase_private
from integrations.firebase.service import firebase_service
from integrations.freshchat import public as freshchat_public
from integrations.wati import public as wati_public
from users import models as user_models


@periodic_task(run_every=crontab(minute="*/5"))
def start_recording_for_streams():
    """Start recording for streams 5 minutes
        before the stream starts.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = now_time + datetime.timedelta(minutes=5)

    # Get all streams start 5 minutes from now.
    streams = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for stream in streams:
        # Start recording for each stream.
        dyte_public.start_recording_for_group(stream)


@periodic_task(run_every=crontab(minute="*/5"))
def send_whatsapp_reminder_for_streams_attendees_and_followers():
    """Send whatsapp reminder to all attendees and followers
        for streams starting in 5 minutes.

    Note:
        Sends reminder to attendees and followers of streams which are
            starting 5 minutes from now.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=5))

    # Send it for all group, except for stream.
    streams = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
        is_published=True,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for stream in streams:
        # Send reminders for followers and attendees for a stream.
        wati_public.send_stream_reminder_messages_for_group(stream)


@periodic_task(run_every=crontab(minute="*/5"))
def send_in_app_reminder_for_stream_attendees_and_followers(groups=None):
    """Send in app notification reminder to all attendees/followers
        for a stream.

    Note:
        Sends reminder to attendees and followers of streams
            which are starting 5 minutes from now.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=5))

    streams = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    ) if not groups else groups

    for stream in streams:
        # Send notification reminders for followers and attendees of a stream.
        notifications_public.send_reminder_notifications_for_stream(stream)


@periodic_task(run_every=crontab(minute="*/30"))
def send_whatsapp_reminder_for_stream_host():
    """Send stream reminders on whatsapp to the hosts.

    Note:
        Sends reminder to hosts of streams which are
            starting 30 minutes from now.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=30))

    # Send it for all group, except for webinars.
    streams = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
        is_published=True,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for stream in streams:
        # Send whatsapp reminder for webinar to host of the stream.
        freshchat_public.send_whatsapp_reminder_for_webinar_host(stream)


@task()
def add_previous_attendees_to_groups(group_ids):
    """Adds host's previous attendees to group.

    Args:
        group_ids(list/queryset): Group ID's for which attendees are
            to be updated.

    """
    groups = models.Group.objects.filter(id__in=group_ids)
    for group in groups:
        prev_groups = models.Group.objects.filter(
            host=group.host,
            start__lt=group.start
        )
        if not prev_groups:
            continue

        # Gather previous groups' attendees
        prev_attendees_list = []
        for prev_group in prev_groups:
            prev_attendees_list += list(prev_group.attendees.all())

        prev_attendees_list = list(set(prev_attendees_list))
        attendees_to_add = list(
            set(prev_attendees_list) - set(list(group.attendees.all()))
        )

        group.attendees.add(*attendees_to_add)
        group.save()


@task()
def publish_group_recordings(group_recording_ids):
    """Uploads dyte recording to media/live_stream_recordings/ for
        a streams. Marks the group recording as published.

    Args:
        group_recording_ids(list/queryset): Group recordings we want to mark
            published.

    Note:
        If a group recording is already published, this doesn't change
            the state.

    """
    group_recordings = models.GroupRecording.objects.filter(id__in=group_recording_ids)
    session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    # Then use the session to get the resource
    s3 = session.resource("s3")
    my_bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)

    for group_recording in group_recordings:
        # If the recording is published continue.
        if group_recording.is_published:
            continue

        dyte_rec = group_recording.dyte_recordings.last()
        if not dyte_rec:
            continue

        file_name = dyte_rec.file_name
        destination = models.recording_storage_path(group_recording, file_name)

        # Copy dyte recording to the live_stream folder.
        try:
            source = {
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": dyte_rec.storage_key_name
            }
            my_bucket.copy(source, "media/" + destination)
        except botocore_exceptions.ClientError:
            path = dyte_constants.DYTE_MEETING_RECORDING_AWS_PATH.format(
                group_id=group_recording.group_id
            )
            source = {
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": path + "/" + dyte_rec.file_name
            }
            my_bucket.copy(source, "media/" + destination)
        except Exception as e:
            logging.error(
                "Exception happened when publishing recording: {} - {}".format(
                    e, group_recording.id
                )
            )
            continue

        # Update the recording.
        group_recording.recording.name = destination
        # Update published.
        group_recording.is_published = True
        group_recording.published_at = datetime.datetime.now()
        group_recording.save()

        # Send recording published signal.
        signals.group_recording_published.send(
            sender=group_recording.__class__,
            recording=group_recording
        )


@periodic_task(run_every=crontab(minute=0, hour="*/3"))
def upload_valid_recordings_for_streams(groups=None):
    """Uploads valid recordings for streams to group_recordings.

    Args:
        groups(list/queryset): List of groups we want to publish
            recordings for.

    Note:
        Only publishes recordings if the recording size is > 100 MB.

    """
    end_time = timezone.now() - timezone.timedelta(hours=3)
    start_time = end_time - timezone.timedelta(hours=3)

    groups = models.Group.objects.filter(
        start__gte=start_time,
        start__lte=end_time,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    ) if not groups else groups

    # Get all group recordings for groups.
    group_recordings = models.GroupRecording.objects.filter(
        group__in=groups,
        is_published=False
    )

    valid_group_recordings = []
    for group_recording in group_recordings:
        # If the recording is published continue.
        if group_recording.is_published:
            continue

        dyte_rec = group_recording.dyte_recordings.last()
        if not dyte_rec:
            continue

        size_in_megabytes = dyte_rec.file_size or 0
        # If the size is less than 150 MB, don't publish.
        if not (size_in_megabytes >= 100):
            continue
        valid_group_recordings.append(group_recording.id)

    # Publish all valid group recordings.
    publish_group_recordings.delay(valid_group_recordings)


@periodic_task(run_every=crontab(hour=0, minute=0))
def add_user_as_follower_for_groups(groups=None):
    """Adds follower object to a creator if the user has
        watched 3 or more streams of the creator.

    """
    now = timezone.now()
    min_start = now - datetime.timedelta(days=1)
    # Get all streams.
    groups = models.Group.objects.filter(
        start__lte=timezone.now(),
        start__gte=min_start,
        host__creator__isnull=False,
        host__creator__is_active=True,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    ) if not groups else groups

    host_creator_ids = groups.values("host", "host__creator").distinct()
    attendees_ids = list(set(groups.values_list("attendees", flat=True)))

    for attendee_id in attendees_ids:
        for host_creator_id in host_creator_ids:
            creator_id = host_creator_id["host__creator"]
            host_id = host_creator_id["host"]

            # Get all streams attended by a user for a host.
            dyte_participants = dyte_models.DyteMeetingParticipant.objects.filter(
                participant_id=attendee_id,
                dyte_meeting__group__host_id=host_id,
                last_online_at__isnull=False
            )

            # If the user hasn't watched minimum 2 streams, don't
            # make the user the follower.
            if dyte_participants.count() < 3:
                continue

            creator_public.get_or_create_follower_for_user(
                attendee_id,
                creator_id
            )


@periodic_task(run_every=crontab(minute="*/5"))
def follow_action_message():
    """Sends follow action message to firebase for live streams.

    Note:
        This sends a message onto freshchat, which is shown in the
            frontend from there.

    """
    live_streams = models.Group.objects.filter(is_live=True, closed=False)
    if not live_streams:
        return

    for stream in live_streams:
        action_time = stream.start + datetime.timedelta(minutes=10)
        end_time = stream.start + datetime.timedelta(minutes=13)

        action_time2 = stream.start + datetime.timedelta(minutes=20)
        end_time2 = stream.start + datetime.timedelta(minutes=23)
        now = timezone.now()

        if not ((action_time <= now < end_time) or (action_time2 <= now < end_time2)):
            continue

        admin_uid = firebase_private.get_or_register_admin()
        data = {
            "message": constants.CHAT_ACTION_FOLLOW_MESSAGE,
            "type": int(constants.CHAT_MESSAGE_TYPE_ACTION_ENUM),
            "action": int(constants.CHAT_ACTION_TYPE_FOLLOW_ENUM)
        }
        firebase_service.send_message(
            data=data,
            group_id=stream.id,
            sender=admin_uid
        )


# @periodic_task(run_every=crontab(minute="*/5"))
def referral_action_message():
    """Sends referral action message to firebase for live streams.

    Note:
        This sends a message onto freshchat, which is shown in the
            frontend from there.

    """
    live_streams = models.Group.objects.filter(is_live=True, closed=False)
    if not live_streams:
        return

    for stream in live_streams:
        action_time = stream.start + datetime.timedelta(minutes=15)
        end_time = stream.start + datetime.timedelta(minutes=18)
        now = timezone.now()

        if not action_time <= now < end_time:
            continue

        admin_uid = firebase_private.get_or_register_admin()
        data = {
            "message": constants.CHAT_ACTION_REFERRAL_MESSAGE,
            "type": int(constants.CHAT_MESSAGE_TYPE_ACTION_ENUM),
            "action": int(constants.CHAT_ACTION_TYPE_REFERRAL_ENUM)
        }
        firebase_service.send_message(
            data=data,
            group_id=stream.id,
            sender=admin_uid
        )


# @periodic_task(run_every=crontab(minute="*/5"))
def chat_prompt_message():
    """Sends chat prompt message to firebase for live streams.

    Note:
        This sends a message onto freshchat, which is shown in the
            frontend from there.

    """
    live_streams = models.Group.objects.filter(is_live=True, closed=False)
    if not live_streams:
        return

    for stream in live_streams:
        action_time = stream.start + datetime.timedelta(minutes=5)
        end_time = stream.start + datetime.timedelta(minutes=8)
        now = timezone.now()

        if not action_time <= now < end_time:
            continue

        admin_uid = firebase_private.get_or_register_admin()
        data = {
            "message": constants.CHAT_PROMPT_MESSAGE,
            "type": int(constants.CHAT_MESSAGE_TYPE_PROMPT_ENUM),
        }

        firebase_service.send_message(
            data=data,
            group_id=stream.id,
            sender=admin_uid
        )


@periodic_task(run_every=crontab(minute="*/5"))
def streams_action_message():
    """Sends other streams action message to firebase for live streams.

    Note:
        This sends a message onto freshchat, which is shown in the
            frontend from there.

    """
    now = timezone.now()
    live_streams = models.Group.objects.filter(is_live=True, closed=False)
    if not live_streams:
        return

    # Get queryset of all future streams and order then by start
    # and highest RSVPs.
    future_streams = models.Group.objects.filter(
        start__gte=now + datetime.timedelta(minutes=30),
        is_published=True,
        privacy=constants.GROUP_PRIVACY_PUBLIC_ENUM
    ).annotate(
        rsvps=Count("attendees")
    ).order_by("start", "-rsvps")

    for stream in live_streams:
        action_time = stream.start + datetime.timedelta(minutes=25)
        end_time = stream.start + datetime.timedelta(minutes=28)
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        categories = stream.categories.all()

        # Check if the action time is valid.
        if not action_time <= now < end_time:
            continue

        # Get streams with the same categories.
        # 1. Get streams that are happening today with the same
        # category. If not found move to 2.
        # 2. Get streams that are happening tomorrow
        # with the same category. If not found move to 3.
        # 3. Get the latest upcoming stream with the highest RSVPs.
        similar_stream = future_streams.filter(
            start__date=today,
            categories__in=categories,
        ).order_by("-rsvps").first() or future_streams.filter(
            start__date=tomorrow,
            categories__in=categories
        ).order_by("-rsvps").first() or future_streams.first()

        admin_uid = firebase_private.get_or_register_admin()
        stream_data = serializers.GroupSerializer(similar_stream).data
        data = {
            "message": constants.CHAT_ACTION_STREAMS_MESSAGE,
            "type": int(constants.CHAT_MESSAGE_TYPE_ACTION_ENUM),
            "action": int(constants.CHAT_ACTION_TYPE_STREAMS_ENUM),
            "data": {
                "stream": json.loads(JSONRenderer().render(stream_data).decode("utf8"))
            }
        }
        firebase_service.send_message(
            data=data,
            group_id=stream.id,
            sender=admin_uid
        )


# @periodic_task(run_every=crontab(minute="*/5"))
def download_app_action_message():
    """Sends download app action message to firebase for live streams.

    Note:
        This sends a message onto freshchat, which is shown in the
            frontend from there.

    """
    live_streams = models.Group.objects.filter(is_live=True, closed=False)
    if not live_streams:
        return

    for stream in live_streams:
        action_time = stream.start + datetime.timedelta(minutes=20)
        end_time = stream.start + datetime.timedelta(minutes=23)
        now = timezone.now()

        if not action_time <= now < end_time:
            continue

        admin_uid = firebase_private.get_or_register_admin()
        data = {
            "message": constants.CHAT_ACTION_DOWNLOAD_APP_MESSAGE,
            "type": int(constants.CHAT_MESSAGE_TYPE_ACTION_ENUM),
            "action": int(constants.CHAT_ACTION_TYPE_DOWNLOAD_APP_ENUM)
        }
        firebase_service.send_message(
            data=data,
            group_id=stream.id,
            sender=admin_uid
        )


# TODO(Sanjeev): Clean this up
# @periodic_task(run_every=crontab(minute="0", hour="13"))
def send_top_stream_message():
    # Get all users who have followed a category
    user_categories = user_models.UserCategory.objects.filter(
        followed=True
    )

    # Filter all active categories
    categories = models.Category.objects.filter(
        is_active=True
    )

    # Get top streams from each category
    top_streams = services.get_top_streams_by_categories(
        categories=categories
    )

    followers = None
    for stream in top_streams:
        if not followers:
            # Filter category followers
            followers = user_categories.filter(
                category=stream["category"]
            )
        else:
            # Filter unique category followers who
            # have not received a top stream message yet.
            followers = user_categories.filter(
                category=stream["category"]
            ).exclude(
                user__in=followers.values_list("user")
            )

        # Add recent users who have watched a stream in
        # this category
        users = services.get_stream_viewers_by_category(
            category=stream["category"]
        )

        # Create a list of unique user ids who will receive
        # the top stream message
        final_user_ids = set(chain(
            followers.values_list("user", flat=True),
            users.values_list("participant", flat=True)
        ))

        # Remove stream host from list if present
        if stream.host in final_user_ids:
            final_user_ids.remove(stream.host)

        wati_public.send_top_stream_message(
            stream=stream,
            user_ids=final_user_ids
        )
