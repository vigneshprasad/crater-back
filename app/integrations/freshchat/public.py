import logging

from integrations.freshchat import constants
from integrations.freshchat import freshchat_service


def send_meeting_whatsapp_reminder_to_user(user, time):
    """Send whatsapp message to user for upcoming meeting."""
    logging.info(
        "Sending Meeting Reminder for User",
        extra={
            "user_email": user.email,
            "data": time
        }
    )
    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REMINDER_FRESHCHAT_TEMPLATE,
        template_data=[{"data": time}]
    )


def send_meeting_opt_in_messages(users):
    """Send whatsapp message to user for meeting opt ins."""
    for user in users:
        freshchat_service.freshchat_whatsapp_service.send_outbound_message(
            user=user,
            template_name=constants.MEETING_OPT_IN_REMINDER_TEMPLATE,
            template_data=[{"data": user.name.title()}]
        )
