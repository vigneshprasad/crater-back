from communications.whatsapp import constants, private
from integrations.freshchat import public as freshchat_public
from integrations.wati import public as wati_public


def send_welcome_crater_whatsapp(user):
    """Sending welcome message to people who
        join Crater.

    Args:
        user(User): User who has signed up on crater.

    """
    provider = private.get_whatsapp_provider_for_message_type(message_type=constants.CRATER_WELCOME_MESSAGE)

    if not provider:
        return

    if provider in [constants.WATI_9501_WHATSAPP_PROVIDER_ENUM, constants.WATI_8953_WHATSAPP_PROVIDER]:
        return wati_public.send_welcome_crater_whatsapp(user=user, account=provider)
    elif provider == constants.FRESHCHAT_WHATSAPP_PROVIDER:
        return freshchat_public.send_welcome_crater_whatsapp(user)


def send_stream_reminder_messages_for_group(group):
    """Send reminder message to attendees and followers of the
        creator doing the stream.

    Args:
        group(Group): Stream we are sending reminders for.

    """
    attendee_provider = private.get_whatsapp_provider_for_message_type(
        message_type=constants.REMINDER_FOR_STREAM_ATTENDEES
    )
    follower_provider = private.get_whatsapp_provider_for_message_type(
        message_type=constants.REMINDER_FOR_STREAM_FOLLOWERS
    )

    # If the provider is not present, don't send the whatsapp message.
    if not attendee_provider:
        return

    if attendee_provider in [constants.WATI_9501_WHATSAPP_PROVIDER_ENUM, constants.WATI_8953_WHATSAPP_PROVIDER_ENUM]:

        # If the follower provider is not the
        if follower_provider not in [constants.WATI_9501_WHATSAPP_PROVIDER_ENUM, constants.WATI_8953_WHATSAPP_PROVIDER_ENUM]:
            follower_provider = attendee_provider

        return wati_public.send_stream_reminder_messages_for_group(
            group,
            attendee_account=attendee_provider,
            follower_account=follower_provider or attendee_provider
        )
    elif attendee_provider == constants.FRESHCHAT_WHATSAPP_PROVIDER_ENUM:
        return freshchat_public.send_whatsapp_reminder_for_webinar_attendees_and_followers(group)


def send_stream_reminder_message_to_host(group):
    """Send reminder message to the host of the stream.

    Args:
        group(Group): Stream we are sending reminders for.

    """
    provider = private.get_whatsapp_provider_for_message_type(message_type=constants.REMINDER_FOR_STREAM_CREATOR)

    if not provider:
        return

    if provider in [constants.WATI_9501_WHATSAPP_PROVIDER_ENUM, constants.WATI_8953_WHATSAPP_PROVIDER]:
        return wati_public.send_stream_reminder_to_group_host(group, account=provider)
    elif provider == constants.FRESHCHAT_WHATSAPP_PROVIDER:
        return freshchat_public.send_whatsapp_reminder_for_webinar_host(group)
