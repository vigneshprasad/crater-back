import logging
import pytz
import urllib.parse

from datetime import datetime
from django.conf import settings

from integrations.freshchat import constants
from integrations.freshchat import freshchat_service
from integrations.freshchat import services
from resources.meetings import services as meeting_services
from utils.tiny_url_service import tiny_url_service
from utils.deep_link_service import deep_link_service


def send_meeting_whatsapp_reminder_to_user(user, meeting):
    """Send whatsapp message to user for upcoming meeting.

    Args:
        user(User): User we are sending the whatsapp reminder to.
        meeting(Meeting): Meeting object for which we are sending the reminder.

    """

    matched_user = meeting.participants.all().exclude(email=user.email).first()
    if not matched_user:
        return

    phone_number = matched_user.get_phone_number().replace("+", "") if user.get_phone_number() else None

    if not phone_number:
        return

    logging.info("Sending meeting reminder to {} for meeting {}".format(user.email, meeting.id))

    # Creating whatsapp prompt for the user.
    whatsapp_prompt_link = tiny_url_service.shorten(
        constants.WHATSAPP_BASE_URL + "{}?".format(phone_number) + "text={}".format(urllib.parse.quote(constants.MEETING_REMINDER_PREFILLED_MESSAGE_PROMPT))
    )
    whatsapp_prompt = constants.MEETING_REMINDER_WHATSAPP_PROMPT_TEXT.format(whatsapp_prompt_link)

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REMINDER_TEMPLATE,
        template_data=[
            {"data": meeting.get_display_start_time()},
            {"data": tiny_url_service.shorten(meeting.link) if meeting.link else ""},
            {"data": matched_user.get_display_first_name()},
            {"data": whatsapp_prompt},
        ]
    )


def send_meeting_opt_in_messages(users):
    """Send whatsapp message to users for conversation opt ins.

    Args:
        users(User queryset): Users to whom this message will go.

    """
    for user in users:
        opt_in_link = services.create_public_opt_in_url(user)
        freshchat_service.freshchat_whatsapp_service.send_outbound_message(
            user=user,
            template_name=constants.CONVERSATION_OPT_IN_TEMPLATE,
            template_data=[
                {"data": opt_in_link},
                {"data": constants.APPSFLYER_APP_LINK},
                {"data": constants.CONVERSATION_OPT_IN_NOTE},
            ]
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

# TODO: Update above function to this once we add topics to 1:1 Meetings

# def send_meeting_confirmation_rsvp(user, meeting):
#     """ Send a message with confirming time and a rsvp link

#     Args:
#         user(User): User to whom this message will go.
#         meeting(Meeting): Meeting for which message confirmation goes

#     """

#     local_tz = pytz.timezone(settings.TIME_ZONE)

#     local_start_datetime = meeting.start.replace(tzinfo=pytz.utc).astimezone(local_tz)
#     local_end_datetime = meeting.end.replace(tzinfo=pytz.utc).astimezone(local_tz)

#     matched_user = meeting.participants.all().exclude(
#             pk=user.pk
#         ).first().get_display_first_name()

#     preference = meeting_services.get_latest_meeting_preference(user)
#     objective = preference.objectives.first()
#     topic = preference.topic.name
#     topic_str = topic if topic else objective
#     topic_str = topic_str if topic_str else constants.MEETING_REGISTRATION_DEFAULT_OBJECTIVE_TEXT

#     date = meeting.start.strftime('%a, %d %b %Y')
#     start_time = local_start_datetime.strftime('%I:%M %p')
#     end_time = local_end_datetime.strftime('%I:%M %p')
#     date_time = "{} - {}, {}".format(start_time, end_time, date)
#     url = services.create_public_rsvp_url(user, meeting)

#     freshchat_service.freshchat_whatsapp_service.send_outbound_message(
#         user=user,
#         template_name=constants.CONVERSATION_CONFIRMATION_11_TEMPLATE,
#         template_data=[
#             {"data": topic_str},
#             {"data": matched_user},
#             {"data": date_time},
#             {"data": constants.APPSFLYER_APP_LINK},
#             {"data": url},
#             {"data": constants.APPSFLYER_APP_LINK},
#         ]
#     )

def send_meeting_confirmation_rsvp(user, meeting):
    """ Send a message with confirming time and a rsvp link

    Args:
        user(User): User to whom this message will go.
        meeting(Meeting): Meeting for which message confirmation goes

    """

    local_tz = pytz.timezone(settings.TIME_ZONE)

    local_start_datetime = meeting.start.replace(tzinfo=pytz.utc).astimezone(local_tz)
    local_end_datetime = meeting.end.replace(tzinfo=pytz.utc).astimezone(local_tz)

    matched_user = meeting.participants.all().exclude(
            pk=user.pk
        ).first().get_display_first_name()

    date = meeting.start.strftime('%a, %d %b %Y')
    start_time = local_start_datetime.strftime('%I:%M %p')
    end_time = local_end_datetime.strftime('%I:%M %p')
    date_time = "{} - {}, {}".format(start_time, end_time, date)
    url = "clicking here - {}".format(services.create_public_rsvp_url(user, meeting))

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_CONFIRMATION_TEMPLATE,
        template_data=[
            {"data": matched_user},
            {"data": date_time},
            {"data": constants.MEETING_INFO_AVAILABILITY},
            {"data": url},
        ]
    )


def send_conversation_confirmation_rsvp_for_group(group):
    """ Send a message with confirmed time and a rsvp link for groups

    Args:
        group(Group): Group for which message confirmation should be sent.

    """
    speakers = group.speakers.all()
    for speaker in speakers:
        send_conversation_confirmation_rsvp_for_user(speaker, group)


def send_conversation_confirmation_rsvp_for_user(user, group):
    """ Send a message with confirming time and a rsvp link for groups

    Args:
        user(User): User to whom this message will go.
        group(Group): Group for which message confirmation goes

    """
    local_start_datetime = group.local_start

    matched_users = group.speakers.all().exclude(pk=user.pk)
    matched_list = []
    for matched_user in matched_users:
        matched_list.append(matched_user)

    if len(matched_list) == 1:
        matched_users_thread = matched_list.pop().get_display_first_name()
    else:
        last_user = matched_list.pop()
        matched_users_thread = ', '.join([matched_user.get_display_first_name() for matched_user in matched_list])
        matched_users_thread = matched_users_thread + " and " + last_user.get_display_first_name()

    topic = group.topic.name

    date = group.start.strftime('%a, %d %b %Y')
    start_time = local_start_datetime.strftime('%I:%M %p')
    date_time = "{}, {}".format(start_time, date)

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.CONVERSATION_CONFIRMATION_TEMPLATE,
        template_data=[
            {"data": topic},
            {"data": matched_users_thread},
            {"data": date_time},
            {"data": constants.CONVERSATION_PARTICIPANTS_APP_LINK.format(
                    tiny_url_service.shorten(constants.APPSFLYER_APP_LINK)
            )},
            {"data": constants.CONVERSATION_RSVP},
        ]
    )


def send_conversation_reminder_for_user(user, group):
    """ Send a message reminding user of upcoming meeting

    Args:
        user(User): User to whom this message will go.
        group(Group): Group for which message confirmation goes

    """
    local_start_datetime = group.local_start

    matched_users = group.speakers.all().exclude(pk=user.pk)
    matched_list = []
    for matched_user in matched_users:
        matched_list.append(matched_user)

    # If there are no users in the group. Don't send this message.
    if not matched_list:
        return
    elif len(matched_list) == 1:
        matched_users_thread = matched_list.pop().get_display_first_name()
    else:
        last_user = matched_list.pop()
        matched_users_thread = ', '.join([matched_user.get_display_first_name() for matched_user in matched_list])
        matched_users_thread = matched_users_thread + " and " + last_user.get_display_first_name()

    topic = group.topic.name

    date = group.start.strftime('%a, %d %b %Y')
    start_time = local_start_datetime.strftime('%I:%M %p')
    date_time = "{}, {}".format(start_time, date)
    group_link = "https://{}/group?id={}".format(settings.FRONT_URL, group.id)
    deeplink = deep_link_service.make_firebase_deep_link(group_link)

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.CONVERSATION_REMINDER_TEMPLATE,
        template_data=[
            {"data": date_time},
            {"data": matched_users_thread},
            {"data": topic},
            {"data": deeplink},
        ]
    )


def send_meeting_rsvp_reminder(user, meeting):
    """ Send a message reminding to rsvp for meeting

    Args:
        user(User): User to whom this message will go.
        meeting(Meeting): Meeting for which message confirmation goes

    """

    url = services.create_public_rsvp_url(user, meeting)

    freshchat_service.freshchat_whatsapp_service.send_outbound_message(
        user=user,
        template_name=constants.MEETING_REMINDER_RSVP_LINK,
        template_data=[
            {"data": url}
        ]
    )
