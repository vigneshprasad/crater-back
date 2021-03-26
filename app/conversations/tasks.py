import datetime
import logging

from celery.schedules import crontab
from celery.task import periodic_task

from conversations import constants
from conversations import models
from integrations.freshchat import constants as freshchat_constants
from integrations.freshchat import public as freshchat_public


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
        matched_users_thread = ', '.join([matched_user.get_display_first_name() for matched_user in matched_list])
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


@periodic_task(run_every=crontab(minute='*/15'))
def send_whatsapp_conversation_reminders(meetings=None):
    """Sends whatsapp reminders for people 30 minutes before their meetings.

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()

    start_datetime = (now_time + datetime.timedelta(minutes=15))
    end_datetime = (now_time + datetime.timedelta(minutes=30))

    groups = models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
    )

    logging.info("Sending reminders for groups between {} - {}. Groups count: {}".format(
            start_datetime, end_datetime, groups.count()
    ))

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


@periodic_task(run_every=crontab(minute='*/5'))
def send_group_feedback_emails(groups=None):
    """Send feedback mails for convesations after 90 minutes of the
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
        end__lt=end_datetime,
    ) if not groups else groups

    logging.info("Sending feedback emails for groups between {} - {}. groups count: {}".format(
        start_datetime, end_datetime, groups.count()
    ))

    exclude_list = []

    for group in groups:

        for speaker in group.speakers.all():
            if speaker in exclude_list:
                continue

            subject = 'How was your group meeting?'

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
                        to: {'email': to}
                    }
                )
