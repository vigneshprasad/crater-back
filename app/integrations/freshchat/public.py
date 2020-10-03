import logging

from datetime import datetime

from integrations.freshchat import constants
from integrations.freshchat import freshchat_service


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
            template_name=constants.MEETING_OPT_IN_REMINDER_TEMPLATE,
            template_data=[{"data": user.get_display_first_name()}]
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
        template_name=constants.MEETING_CONFIRMATION_FRESHCHAT_TEMPLATE,
        template_data=[
            {"data": user.name},
            {"data": time},
            {"data": date},
        ]
    )