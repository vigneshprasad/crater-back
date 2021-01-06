import logging

from django.conf import settings
from django.dispatch import receiver

from users import signals as user_signals
from integrations.freshchat import constants
from integrations.freshchat import freshchat_service
from integrations.freshchat import tasks
from resources.meetings import signals as meeting_signals
from resources.meetings import choices as meeting_constants

@receiver(user_signals.user_updated)
def create_or_update_freshchat_user(sender, user, *args, **kwargs):
    """Creates or Updates freshchat user if the user is updated
        on our end.

    """
    if not user.has_profile:
        return

    if not settings.FRESHCHAT_USER_CREATION_ALLOWED:
        return

    tasks.create_or_update_freshchat_user.delay(user.pk)


@receiver(meeting_signals.registered_for_meeting)
def send_registration_confirmation(sender, user, **kwargs):
    """Send a whatsapp message with confirmation once a
        user registers for a meeting.

    """
    created = kwargs.pop("created", None)
    if not created:
        return

    meeting_preference = sender

    looking_for_objectives = meeting_preference.objectives.filter(type=meeting_constants.OBJECTIVE_TYPES[0][0]).first()
    looking_to_objectives = meeting_preference.objectives.filter(type=meeting_constants.OBJECTIVE_TYPES[1][0]).first()

    objectives_str = "{} & {}".format(looking_for_objectives, looking_to_objectives) \
        if (looking_for_objectives and looking_to_objectives) else constants.MEETING_REGISTRATION_DEFAULT_OBJECTIVE_TEXT

    logging.info("Send a message to a user who has created a meeting preference".format(user.email))

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REGISTRATION_TEMPLATE,
        template_data=[
            {"data": constants.MEETING_REGISTRATION_FREQUENCY_PLACEHOLDER},
            {"data": objectives_str},
            {"data": "the mobile app here: {}".format(constants.APPSFLYER_APP_LINK)}
        ]
    )


@receiver(meeting_signals.meeting_marked_cancelled)
def send_meeting_cancellation_message(sender, user, meeting, *args, **kwargs):
    """Send whatsapp message to user for upcoming meeting.

    Args:
        sender(Meeting Class): Meeting class object for the meeting message is being sent.
        user(User): User that has cancelled the meeting.
        meeting(Meeting): Meeting object for which we are sending the reminder.

    """
    participants = meeting.participants.all()
    for participant in participants:
        freshchat_service.freshchat_whatsapp_service.send_outbound_message(
            user=participant,
            template_name=constants.MEETING_CANCELLATION_TEMPLATE,
            template_data=[
                {"data": "you" if (user.pk == participant.pk) else participant.get_display_first_name()},
                {"data": constants.MEETING_CANCELLATION_FALL_BACK}
            ]
        )
