from integrations.freshchat import constants
from integrations.freshchat import _freshchat_service


def send_meeting_whatsapp_reminder_to_user(user, time):
    """Send whatsapp message to user for upcoming meeting."""
    template_data = [{"data": time}]
    response = _freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REMINDER_FRESHCHAT_TEMPLATE,
        template_data=template_data
    )
    return response
