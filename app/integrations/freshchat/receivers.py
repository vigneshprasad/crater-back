import datetime
import logging

import pytz
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver

from users import signals as user_signals
from users import constants as user_constants
from integrations.freshchat import constants
from integrations.freshchat import freshchat_service
from integrations.freshchat import services
from integrations.freshchat import tasks
from resources.meetings import signals as meeting_signals
from resources.meetings import choices as meeting_constants
from conversations import signals as conversation_signals
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


@receiver(user_signals.phone_number_verified)
def send_worknetwork_registration_confirmation(sender, user, **kwargs):
    """Send a whatsapp message with confirmation once a
        user registers for a meeting.

    """
    logging.info("Send a message to a user who has verified phone number".format(
        user.email,
    ))

    return freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.REGISTRATION_CONFIRMATION,
        template_data=[
            {"data": constants.REGISTRATION_TEMPLATE_DEFAULT_TOPIC},
            {"data": user.email},
            {"data": constants.LANDING_PAGE},
            {"data": constants.APPSFLYER_APP_LINK},
        ]
    )


@receiver(conversation_signals.new_conversation_registration)
def send_conversation_registration_confirmation(sender, preference, **kwargs):
    """Send a whatsapp message with confirmation once a
        user registers for a conversation(group).

    """
    user = preference.user

    logging.info("Send a message to a user who has created a meeting preference".format(
        user.email,
    ))

    if user.new_source and user.new_source.base_source and user.new_source.base_source.name == user_constants.BASE_SOURCE_KODO:
        return
        
    objective = preference.objectives.first()
    topic = preference.topic

    topic_str = topic.name if topic else objective.name
    topic_str = topic_str if topic_str else constants.MEETING_REGISTRATION_DEFAULT_OBJECTIVE_TEXT

    time_slots = preference.time_slots.all()
    time_list = [time_slot.get_display() for time_slot in time_slots] if time_slots else "No Time Slots Selected." 
    time_str = ", ".join(time_list)

    logging.info("Send a message to a user who has created a meeting preference".format(user.email))

    return freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.CONVERSATION_REGISTRATION_TEMPLATE,
        template_data=[
            {"data": topic_str},
            {"data": time_str},
        ]
    )


# TODO: To delete once we migrate MeetingPreference
@receiver(meeting_signals.new_meeting_registration)
def send_registration_confirmation(sender, preference, **kwargs):
    """Send a whatsapp message with confirmation once a
        user registers for a meeting(1:1).

    """
    user = preference.user

    logging.info("Send a message to a user who has created a meeting preference".format(
        user.email,
    ))

    if user.new_source and user.new_source.base_source and user.new_source.base_source.name == user_constants.BASE_SOURCE_KODO:
        return

    looking_for_objective = preference.objectives.filter(type=meeting_constants.OBJECTIVE_TYPES[0][0]).first()
    looking_to_objective = preference.objectives.filter(type=meeting_constants.OBJECTIVE_TYPES[1][0]).first()

    objectives_str = "{} & {}".format(looking_for_objective.name, looking_to_objective.name) \
        if (looking_for_objective and looking_to_objective) else constants.MEETING_REGISTRATION_DEFAULT_OBJECTIVE_TEXT

    logging.info("Send a message to a user who has created a meeting preference".format(user.email))

    return freshchat_service.freshchat_whatsapp_service.send_outbound_message(
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
            {"data": "you" if (rsvp1.status == meeting_constants.MEETING_RSVP_STATUS_NOT_ATTENDING or
                               (rsvp1.status == meeting_constants.MEETING_RSVP_STATUS_PENDING and
                                rsvp2.status != meeting_constants.MEETING_RSVP_STATUS_NOT_ATTENDING))
                else participant2.get_display_first_name()},
            {"data": constants.MEETING_CANCELLATION_FALL_BACK}
        ]
    )

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=participant2,
        template_name=constants.MEETING_CANCELLATION_TEMPLATE,
        template_data=[
            {"data": "you" if (rsvp2.status == meeting_constants.MEETING_RSVP_STATUS_NOT_ATTENDING or
                               (rsvp2.status == meeting_constants.MEETING_RSVP_STATUS_PENDING and
                                rsvp1.status != meeting_constants.MEETING_RSVP_STATUS_NOT_ATTENDING))
                else participant1.get_display_first_name()},
            {"data": constants.MEETING_CANCELLATION_FALL_BACK}
        ]
    )

    return True


@receiver(meeting_signals.reschedule_request_created)
def send_reschedule_requested_message(sender, reschedule_request, *args, **kwargs):
    approver = reschedule_request.approver
    requested_by = reschedule_request.requested_by

    public_reschedule_url = services.create_public_reschedule_url(reschedule_request)

    return freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=approver,
        template_name=constants.MEETING_RESCHEDULE_REQUEST_TEMPLATE,
        template_data=[
            {"data": requested_by.get_display_first_name()},
            {"data": " by clicking on this link: {}".format(public_reschedule_url)}
        ]
    )


@receiver(meeting_signals.reschedule_request_approved)
def send_reschedule_request_approved_message(sender, reschedule_request, **kwargs):
    """Send approval message on acceptance of reschedule request."""
    approver = reschedule_request.approver
    requested_by = reschedule_request.requested_by
    meeting = reschedule_request.new_meeting

    return freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=requested_by,
        template_name=constants.MEETING_RESCHEDULE_REQUEST_APPROVED_TEMPLATE,
        template_data=[
            {"data": approver.get_display_first_name()},
            {"data": meeting.get_display_start_time()},
            {"data": meeting.get_display_day()},
            {"data": tiny_url_service.shorten(meeting.link)}
        ]
    )


@receiver(meeting_signals.reschedule_request_declined)
def send_reschedule_request_declined_message(sender, reschedule_request, *args, **kwargs):
    approver = reschedule_request.approver
    requested_by = reschedule_request.requested_by

    return freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=requested_by,
        template_name=constants.MEETING_RESCHEDULE_REQUEST_DECLINED_TEMPLATE,
        template_data=[
            {"data": approver.get_display_first_name()},
            {"data": constants.MEETING_RESCHEDULE_REQUEST_DECLINED_PROMPT_MESSAGE},
        ]
    )


@receiver(meeting_signals.meeting_request_created)
def send_meeting_request_created_message(sender, meeting_request, *args, **kwargs):
    pass


@receiver(meeting_signals.meeting_request_approved)
def send_meeting_request_approved_message(sender, meeting_request, *args, **kwargs):
    pass


@receiver(meeting_signals.meeting_request_declined)
def send_meeting_request_declined_message(sender, meeting_request, *args, **kwargs):
    pass


@receiver(conversation_signals.attendee_added_to_group)
def send_whatsapp_for_webinar_rsvp_to_attendee(sender, group, user, *args, **kwargs):
    """Send whatsapp to attendee for RSVPing to the webinar.

    Args:
        sender(Group class): Class object for group.
        group(Group): Webinar group we are creating dyte meeting
            for.
        user(User): User that got added to the group.

    """

    # If the webinar is already live, don't send this message.
    utc = pytz.utc
    if datetime.datetime.now(tz=utc) > group.start:
        return

    attendee_name = user.get_display_first_name()
    host = group.host
    if not host:
        return

    host_name = host.display_name
    display_start = group.get_display_start()
    topic_name = group.topic.name
    stream_link = "https://crater.club/session/{group_id}".format(
        group_id=group.id
    )
    stream_message = "The stream will go live here: {}".format(stream_link)
    data_4 = "{}. {}".format(topic_name, stream_message)

    return freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.WEBINAR_ATTENDEE_RSVP_CONFIRMATION_TEMPLATE,
        template_data=[
            {"data": attendee_name},
            {"data": host_name},
            {"data": display_start},
            {"data": data_4}
        ]
    )
