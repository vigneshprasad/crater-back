import datetime
import json
import logging

import boto3
from asgiref.sync import async_to_sync
from celery.schedules import crontab
from celery.task import periodic_task
from celery.task import task
from django.conf import settings
from channels.layers import get_channel_layer

from conversations import constants
from conversations import models
from conversations import services
from integrations.dyte import public as dyte_public
from integrations.freshchat import constants as freshchat_constants
from integrations.freshchat import public as freshchat_public
from resources.meetings import services as meeting_services
from users import constants as user_constants
from users import models as user_models


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


@periodic_task(run_every=crontab(minute="*/15"))
def send_whatsapp_reminder_for_webinar_attendees(groups=None):
    """Send whatsapp reminder to all attendees for Webinar

    Note:
        Sends reminder to attendees of webinar which is
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
        freshchat_public.send_whatsapp_reminder_for_webinar_attendees_and_followers(
            webinar
        )


@periodic_task(run_every=crontab(minute="*/10"))
def send_whatsapp_reminder_for_webinar_host(groups=None):
    """Send webinar reminder whatsapp for the host.

    Note:
        Sends reminder to host of webinar which is
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


@periodic_task(run_every=crontab(minute="*/15"))
def send_group_feedback_emails(groups=None):
    """Send feedback mails for conversations after 90 minutes of the
        meeting.

    Args:
        groups(Group queryset): Queryset of groups you want to send this
            reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()

    start_datetime = (now_time - datetime.timedelta(minutes=105))
    end_datetime = (now_time - datetime.timedelta(minutes=90))

    groups = models.Group.objects.filter(
        end__gte=start_datetime,
        end__lt=end_datetime
    ).exclude(type=constants.GROUP_TYPE_WEBINAR_ENUM) if not groups else groups

    logging.info("Sending feedback emails for groups between {} - {}. groups count: {}".format(
        start_datetime, end_datetime, groups.count()
    ))

    exclude_list = []

    for group in groups:

        for speaker in group.speakers.all():
            if speaker in exclude_list:
                continue

            subject = "How was your group meeting?"

            to_emails = [speaker.email]
            from_email = constants.MEETING_COMMUNICATION_FROM_EMAIL

            template_name = constants.GROUP_CONVERSATION_FEEDBACK_TEMPLATE

            # Sending the emails.
            for to in to_emails:
                speaker.send_email(
                    subject=subject,
                    to=[to],
                    template_name=template_name,
                    content={},
                    from_email=from_email,
                    merge_vars={
                        to: {"email": to}
                    }
                )


# TODO(Nishant): Cleanup this during refactor of code.
@periodic_task(run_every=crontab(hour=10, minute=30))
def create_user_introductions_for_eligible_users(profiles=None):
    """Create introductions for users without introduction."""
    profiles = user_models.Profile.objects.all() if not profiles else profiles

    for profile in profiles:
        if profile.introduction or profile.generated_introduction:
            continue

        user = profile.user
        first_name = user.get_display_first_name()
        # Get tag data.
        user_tag = profile.new_tag.first()
        if not user_tag:
            return
        user_tag_name = user_tag.name

        user_experience = profile.years_of_experience
        if not user_experience:
            continue
        user_experience_str = dict(user_models.Profile.YEARS_OF_EXPERIENCE_CHOICES).get(profile.years_of_experience)

        user_company_type = profile.company_type
        if not user_company_type:
            continue
        user_company_type_str = dict(user_models.Profile.COMPANY_TYPE_CHOICES).get(profile.company_type)

        user_sector = profile.sector
        if not user_sector:
            continue
        user_sector_str = dict(user_models.Profile.SECTOR_CHOICES).get(profile.sector)

        user_education = profile.education_level
        if not user_education:
            continue
        user_education_str = dict(user_models.Profile.EDUCATION_LEVEL_CHOICES).get(profile.education_level)

        user_meetings = meeting_services.get_meetings_for_users(user)
        user_groups = models.Group.objects.filter(speakers=user)

        conversation_count = (user_meetings.count() + user_groups.count())

        if conversation_count:
            conversation_str = "{}+ conversations".format(conversation_count)
        else:
            conversation_str = "First conversation"

        introduction_string = user_constants.DEFAULT_INTRODUCTION_STR.format(
            first_name=first_name,
            tag=user_tag_name,
            experience=user_experience_str,
            company_type=user_company_type_str,
            sector=user_sector_str,
            education=user_education_str,
            conversation_str=conversation_str
        )

        profile.generated_introduction = introduction_string
        profile.save()


# @periodic_task(run_every=datetime.timedelta(seconds=10))
def cache_participant_count():
    """Calculate current participant count for live webinars.

    Note:
        The function creates it every 10 seconds and updates
            participant count for each webinar.

    """
    cached_live_webinars = settings.REDIS.get("live_webinars")

    if not cached_live_webinars:
        return

    live_webinars = json.loads(cached_live_webinars.decode("ascii")).get("webinars")

    for data in live_webinars:
        current = sec = 0

        # Check cache for the webinar id and get the cached values.
        cached_value = settings.REDIS.get(f"{data.get('group_id')}")

        if cached_value is not None:
            obj = json.loads(cached_value.decode("ascii"))
            current = obj.get("current")
            sec = obj.get("sec")

        current, sec = services.participant_count(
            data.get("participant"),
            current,
            sec
        )

        # Set the updated current count and sec to redis cache.
        settings.REDIS.set(
            f"{data.get('group_id')}",
            json.dumps({"current": current, "sec": sec})
        )

        # Send the current live count to channel layer group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"{data.get('group_id')}",
            {
                "type": "send.live_count",
                "text": json.dumps({
                    "type": "live_count",
                    "count": current
                })
            }
        )


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
    """Uploads dyte recording to media/live_stream/ for
        a streams.

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

        source = {
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": dyte_rec.storage_key_name
        }
        destination = models.recording_storage_path(group_recording, file_name)

        # Copy dyte recording to the live_stream folder.
        try:
            my_bucket.copy(source, "media/" + destination)
        except Exception:
            continue

        # Update the recording.
        group_recording.recording.name = destination
        # Update published.
        group_recording.is_published = True
        group_recording.published_at = datetime.datetime.now()
        group_recording.save()
