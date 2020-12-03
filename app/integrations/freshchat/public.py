import logging

from datetime import datetime

from integrations.freshchat import constants
from integrations.freshchat import freshchat_service
from integrations.freshchat.services import create_public_url

from freelance.settings import FRONT_URL


def send_meeting_whatsapp_reminder_to_user(user, time):
    """Send whatsapp message to user for upcoming meeting.

    Args:
        user(User): User we are sending the whatsapp reminder to.
        time(str): Str time for the meeting start time.

    """
    logging.info("Sending meeting reminder for {}, meeting starting at {}".format(user.email, time))
    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REMINDER_FRESHCHAT_TEMPLATE,
        template_data=[{"data": time}]
    )


def send_meeting_opt_in_messages(users):
    """Send whatsapp message to users for 1:1 meeting opt ins.

    Args:
        users(User queryset): Users to whom this message will go.

    """
    for user in users:
        freshchat_service.freshchat_whatsapp_service.send_outbound_message(
            user=user,
            template_name=constants.MEETING_CONFIRMATION_INTENT,
            template_data=[]
        )


def send_meeting_time_confirmation(user, start_time, end_time):
    """Send meeting time slot confirmation messages.

    Args:
        user(User): User to whom this message will go.
        start_time(datetime): Start datetime object for meeting
        end_time(datetime): End datetime object for meeting

    """
    logging.info("Send meeting time confirmation for user {} and Time: {} - {}".format(
        user.email, start_time, end_time
    ))

    date = start_time.strftime('%a, %d %b %Y')
    start_time = start_time.strftime('%I:%M %p')
    end_time = end_time.strftime('%I:%M %p')
    time = "{} - {}".format(start_time, end_time)
    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_CONFIRMATION_WITH_EMAIL_SENT,
        template_data=[
            {"data": date},
            {"data": time},
        ]
    )


def send_registration_confirmation(user):
    """Send a message once user has created a meeting preference

    Args:
        user(User): User to whom this message will go.
    """
    logging.info("Send a message to a user who has created a meeting preference".format(
        user.email,
    ))

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.REGISTRATION_CONFIRMATION,
        template_data= [
            {"data": 'https://{}/meetings'.format(FRONT_URL) }
        ]
    )


def send_meeting_confirmation_rsvp(user, meeting):
    """ Send a message with confirming time and a rsvp link

    Args:
        user(User): User to whom this message will go.
        meeting(Meeting): Meeting for which message confirmation goes
    """

    date = meeting.start.strftime('%a, %d %b %Y')
    start_time = meeting.start.strftime('%I:%M %p')
    end_time = meeting.end.strftime('%I:%M %p')
    time = "{} - {}".format(start_time, end_time)
    url = create_public_url(user, meeting)

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_CONFIRMATION_RSVP_LINK,
        template_data=[
            {"data": date},
            {"data": time},
            {"data": url},
        ]
    )


def send_meeting_rsvp_reminder(user, meeting):
    """ Send a message reminding to rsvp for meeting

    Args:
        user(User): User to whom this message will go.
        meeting(Meeting): Meeting for which message confirmation goes

    """

    url = create_public_url(user, meeting)

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REMINDER_RSVP_LINK,
        template_data=[
            {"data": url}
        ]
    )
