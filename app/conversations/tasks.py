import datetime
import logging

import boto3
from botocore import exceptions as botocore_exceptions
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.utils import timezone

from conversations import constants, models
from crater.creator import public as creator_public
from integrations.dyte import constants as dyte_constants, models as dyte_models, public as dyte_public
from integrations.firebase import private as firebase_private
from integrations.firebase.service import firebase_service
from integrations.freshchat import constants as freshchat_constants, public as freshchat_public
from integrations.wati import public as wati_public


def send_conversation_confirmation_email_for_group(group):
    """Send confirmation for conversation.

    Args:
       group(Group): Group for which we have send confirmation.

    """
    speakers = group.speakers.all()
    for speaker in speakers:
        send_conversation_confirmation_email_for_user(speaker, group)


def send_conversation_confirmation_email_for_user(user, group):
    """Send confirmation for conversation.

    Args:
       user(User): User to send the email to.
       group(Group): Group for which we have send confirmation.

    """
    local_start_datetime = group.local_start

    matched_users = group.speakers.all().exclude(pk=user.pk)

    matched_list = []
    for matched_user in matched_users:
        matched_list.append(matched_user)

    if len(matched_list) == 1:
        matched_users_thread = matched_list.pop().get_display_first_name()
    else:
        last_user = matched_list.pop()
        matched_users_thread = ", ".join([matched_user.get_display_first_name() for matched_user in matched_list])
        matched_users_thread = matched_users_thread + " and " + last_user.get_display_first_name()

    topic = group.topic.name

    date = group.start.strftime("%a, %d %b %Y")
    start_time = local_start_datetime.strftime("%I:%M %p")
    time = "{}, {}".format(start_time, date)

    subject = "Your upcoming conversation on {}".format(topic)

    to_emails = [user.email, constants.EXTRA_EMAIL_FOR_INTRO_VERIFICATION]
    # Populating data.
    data = {
        user.email:
            {
                "name": user.get_display_first_name(),
                "topic": topic,
                "time": time,
                "description": group.topic.description,
                "participants": matched_users_thread,
                "app_link": freshchat_constants.APPSFLYER_APP_LINK,
                "email": user.email
            },
        constants.EXTRA_EMAIL_FOR_INTRO_VERIFICATION:
            {
                "name": user.get_display_first_name(),
                "topic": topic,
                "time": time,
                "description": group.topic.description,
                "participants": matched_users_thread,
                "app_link": freshchat_constants.APPSFLYER_APP_LINK,
                "email": user.email
            }
    }

    from_email = constants.MEETING_COMMUNICATION_FROM_EMAIL
    reply_to_email = [constants.MEETING_REPLY_EMAIL]

    template_name = constants.GROUP_CONVERSATION_INTRODUCTION_TEMPLATE

    # Sending the emails.
    for to in to_emails:
        user.send_email(
            subject=subject,
            to=[to],
            reply_to=reply_to_email,
            template_name=template_name,
            content={},
            from_email=from_email,
            merge_vars=data
        )


@periodic_task(run_every=crontab(minute="*/5"))
def start_recording_for_webinars(groups=None):
    """Start recording for webinars 5 minutes
        before the webinar starts.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=5))

    # Get all webinars start 5 minutes from now.
    webinars = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for webinar in webinars:
        # Start recording for each webinar.
        dyte_public.start_recording_for_group(
            webinar
        )


@periodic_task(run_every=crontab(minute="*/10"))
def send_whatsapp_reminder_for_webinar_attendees(groups=None):
    """Send whatsapp reminder to all attendees for Webinar

    Note:
        Sends reminder to attendees of webinar which is
            starting 10 minutes from now.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=10))

    # Send it for all group, except for webinars.
    webinars = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for webinar in webinars:
        # Send reminders for followers and attendees.
        wati_public.send_stream_reminder_messages_for_group(webinar)


@periodic_task(run_every=crontab(minute="*/15"))
def send_whatsapp_reminder_for_webinar_host(groups=None):
    """Send webinar reminder whatsapp for the host.

    Note:
        Sends reminder to host of webinar which is
            starting 15 minutes from now.

    """
    now_time = datetime.datetime.now()

    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=15))

    # Send it for all group, except for webinars.
    webinars = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for webinar in webinars:
        # Send whatsapp reminder for webinar to attendees.
        freshchat_public.send_whatsapp_reminder_for_webinar_host(
            webinar
        )


@periodic_task(run_every=crontab(minute="*/10"))
def send_whatsapp_conversation_reminders(meetings=None):
    """Sends whatsapp reminders for people 30 minutes before their meetings.

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()

    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=10))

    # Send it for all group, except for webinars.
    groups = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime
    ).exclude(type=constants.GROUP_TYPE_WEBINAR_ENUM)

    # Log id's of the groups we are sending reminders for.
    logging.info(
        "Sending reminders for groups between {} - {}. Group ID's: {}".format(
            start_datetime, end_datetime, [group.id for group in groups]
        )
    )

    exclude_list = []

    for group in groups:
        for speaker in group.speakers.all():
            if speaker in exclude_list:
                continue
            freshchat_public.send_conversation_reminder_for_user(
                speaker,
                group
            )
            exclude_list.append(speaker)


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
        except botocore_exceptions.ClientError as e:
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


@periodic_task(run_every=crontab(minute=0, hour="*/3"))
def upload_valid_recordings_for_streams(groups=None):
    """Uploads valid recordings for streams to group_recordings.

    Args:
        groups(list/queryset): List of groups we want to publish
            recordings for.

    Note:
        Only publishes recordings if the recording size is >150 MB.

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

    # Get the session for S3.
    session = boto3.Session(
        aws_access_key_id=settings.DYTE_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.DYTE_AWS_SECRET_ACCESS_KEY
    )
    # Then use the session to get the resource
    s3 = session.resource("s3")

    valid_group_recordings = []
    for group_recording in group_recordings:
        # If the recording is published continue.
        if group_recording.is_published:
            continue

        dyte_rec = group_recording.dyte_recordings.last()
        if not dyte_rec:
            continue

        try:
            recording_object_s3 = s3.Object(settings.AWS_STORAGE_BUCKET_NAME, dyte_rec.storage_key_name)
            size_in_bytes = recording_object_s3.content_length
        except botocore_exceptions.ClientError as e:
            path = dyte_constants.DYTE_MEETING_RECORDING_AWS_PATH.format(
                group_id=group_recording.group_id
            )
            recording_object_s3 = s3.Object(
                settings.AWS_STORAGE_BUCKET_NAME,
                path + "/" + dyte_rec.file_name
            )
            size_in_bytes = recording_object_s3.content_length
        except Exception as e:
            logging.error(
                "Exception happened when uploading recording: {} - {}".format(
                    e, group_recording.id
                )
            )
            continue

        size_in_megabytes = size_in_bytes / (1024 * 1024)
        # If the size is less than 150 MB, don't publish.
        if not (size_in_megabytes >= 100):
            continue
        valid_group_recordings.append(group_recording.id)

    # Publish all valid group recordings.
    publish_group_recordings.delay(valid_group_recordings)


@periodic_task(run_every=crontab(hour=5, minute=30))
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
    live_streams = models.Group.objects.filter(
        is_live=True,
        closed=False,
    )

    if not live_streams:
        return

    for stream in live_streams:
        action_time = stream.start + datetime.timedelta(minutes=10)
        end_time = stream.start + datetime.timedelta(minutes=13)
        now = timezone.now()

        if not action_time <= now < end_time:
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
    live_streams = models.Group.objects.filter(
        is_live=True,
        closed=False,
    )

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


@periodic_task(run_every=crontab(minute="*/5"))
def streams_action_message():
    live_streams = models.Group.objects.filter(
        is_live=True,
        closed=False,
    )

    if not live_streams:
        return

    for stream in live_streams:
        action_time = stream.start + datetime.timedelta(minutes=25)
        end_time = stream.start + datetime.timedelta(minutes=28)
        now = timezone.now()

        if not action_time <= now < end_time:
            continue

        admin_uid = firebase_private.get_or_register_admin()

        data = {
            "message": constants.CHAT_ACTION_STREAMS_MESSAGE,
            "type": int(constants.CHAT_MESSAGE_TYPE_ACTION_ENUM),
            "action": int(constants.CHAT_ACTION_TYPE_STREAMS_ENUM)
        }

        firebase_service.send_message(
            data=data,
            group_id=stream.id,
            sender=admin_uid
        )


@periodic_task(run_every=crontab(minute="*/5"))
def download_app_action_message():
    live_streams = models.Group.objects.filter(
        is_live=True,
        closed=False,
    )

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
