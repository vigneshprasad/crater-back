import logging

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
            template_data=[{"data": user.name.title()}]
        )
