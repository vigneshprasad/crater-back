from communications.whatsapp import models


def get_whatsapp_provider_for_message_type(message_type):
    """Get the active whatsapp provider we are using."""
    whatsapp_provider_for_message_type = models.WhatsappProvider.objects.get(
        message_type=message_type
    )
    if not whatsapp_provider_for_message_type:
        return

    return whatsapp_provider_for_message_type.provider
