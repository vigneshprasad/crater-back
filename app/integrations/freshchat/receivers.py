import logging

from django.conf import settings
from django.dispatch import receiver

from users import signals as user_signals
from integrations.freshchat import constants
from integrations.freshchat import freshchat_service
from integrations.freshchat import tasks
from resources.meetings import signals as meeting_signals
from resources.meetings import choices as meeting_constants
from utils.tiny_url_service import tiny_url_service


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


@receiver(meeting_signals.new_meeting_registration)
def send_registration_confirmation(sender, preference, **kwargs):
    """Send a whatsapp message with confirmation once a
        user registers for a meeting.

    """
    user = preference.user

    logging.info("Send a message to a user who has created a meeting preference".format(
        user.email,
    ))

    looking_for_objective = preference.objectives.filter(type=meeting_constants.OBJECTIVE_TYPES[0][0]).first()
    looking_to_objective = preference.objectives.filter(type=meeting_constants.OBJECTIVE_TYPES[1][0]).first()

    objectives_str = "{} & {}".format(looking_for_objective.name, looking_to_objective.name) \
        if (looking_for_objective and looking_to_objective) else constants.MEETING_REGISTRATION_DEFAULT_OBJECTIVE_TEXT

    logging.info("Send a message to a user who has created a meeting preference".format(user.email))

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REGISTRATION_TEMPLATE,
        template_data=[
            {"data": constants.MEETING_REGISTRATION_FREQUENCY_PLACEHOLDER},
            {"data": objectives_str},
            {"data": "the mobile app here: {}".format(tiny_url_service.shorten(constants.APPSFLYER_APP_LINK))}
        ]
    )


@receiver(meeting_signals.meeting_marked_cancelled)
def send_meeting_cancellation_message(sender, meeting, *args, **kwargs):
    """Send whatsapp message to user for upcoming meeting.

    Args:
        sender(Meeting Class): Meeting class object for the meeting message is being sent.
        user(User): User that has cancelled the meeting.
        meeting(Meeting): Meeting object for which we are sending the reminder.

    """

    participant1 = meeting.participants.first()
    participant2 = meeting.participants.last()

    rsvp1 = participant1.meeting_rsvps.filter(meeting=meeting).first()
    rsvp2 = participant2.meeting_rsvps.filter(meeting=meeting).first()

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=participant1,
        template_name=constants.MEETING_CANCELLATION_TEMPLATE,
        template_data=[
            {"data": "you" if (
                    rsvp1.status == meeting_constants.MEETING_RSVP_STATUS_NOT_ATTENDING
            ) else participant2.get_display_first_name()},
            {"data": constants.MEETING_CANCELLATION_FALL_BACK}
        ]
    )

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=participant2,
        template_name=constants.MEETING_CANCELLATION_TEMPLATE,
        template_data=[
            {"data": "you" if (
                    rsvp2.status == meeting_constants.MEETING_RSVP_STATUS_NOT_ATTENDING
            ) else participant1.get_display_first_name()},
            {"data": constants.MEETING_CANCELLATION_FALL_BACK}
        ]
    )
