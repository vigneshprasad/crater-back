from django.dispatch import receiver

from .models import TrackLog, IdentifyLog
from community.posts import signals as post_signals
from conversations import signals as conversation_signals
from resources.meetings import signals as meetings_signals
from creative_exchange import signals as creative_exchange_signals
from users import models as user_models
from users import signals as user_signals
from utils.segment_service import segment_service
from wn_analytics import constants
from wn_analytics.utils import get_user_traits


def analytics_track(user, event, analytics_track_properties=None):
    """Tracks an event to Segment.

    Args:
        user(User): User object who did the event.
        event(str): Event name as registered on segment.
        analytics_track_properties(dict): Extra properties
            for the event.

    """

    user_id = str(user.pk)
    # TODO(Nishant): Will reuse this code when Flutter app is released.
    # Added user devices info to the track properties.
    # _add_user_device_info(user, analytics_track_properties)

    analytics_track_properties = analytics_track_properties if analytics_track_properties else {}
    segment_service.track(
        user_id=user_id, 
        event=event,
        properties=analytics_track_properties
    )
    track_log = TrackLog.objects.create(
        user=user,
        event=event,
        properties=analytics_track_properties
    )
    return track_log


@receiver(user_signals.user_updated)
def analytics_identify(sender, user, **kwargs):
    """Registers and updated segment profile of a user.

    Args:
        sender(Class): Class representation of user.
        user(User): User who updated/created his profile.

    """
    user_id = str(user.pk)
    traits = get_user_traits(user)

    segment_service.identify(
        user_id=user_id, 
        traits=traits
    )
    identify_log = IdentifyLog.objects.create(
        user=user,
        traits=traits
    )
    return identify_log


@receiver(user_signals.user_signed_up)
def user_signed_up_track(sender, user, **kwargs):
    event = constants.USER_CREATED
    analytics_track_properties = {
        "email": user.email, 
        "role": user.role,
        "name": user.name,
        "source": user.source
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(user_signals.email_verified)
def email_verified_track(sender, email_address, **kwargs):
    event = constants.EMAIL_VERIFIED
    user = user_models.User.objects.get(email=email_address.email)
    analytics_track_properties = {
        "email": email_address.email, 
        "role": user.role,
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(user_signals.objectives_added)
def objectives_added_track(sender, user, objectives, **kwargs):
    event = constants.OBJECTIVES_ADDED
    analytics_track_properties={
        "objectives": objectives,
        "email": user.email,
        "intent": user.intent
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(user_signals.basic_profile_created)
def basic_profile_track(sender, user, request, response, **kwargs):
    analytics_track_properties = {
        "name": response.data["name"],
        "focus": response.data["focus"],
        "introduction": response.data["introduction"],
        "tag_line": response.data["tag_line"],
        "twitter": response.data["twitter"],
        "instagram_id": response.data["instagram_id"],
        "additional_information": response.data["additional_information"],
        "photo": response.data["photo"],
        "work_city": response.data["work_city_name"]
    }
    tag_list = response.data["tag_list"]
    tags = []
    for tag in tag_list:
        tags.append(tag["name"])
    analytics_track_properties["tags"] = tags

    event = constants.BASIC_PROFILE_CREATED
    analytics_track(user, event, analytics_track_properties)


@receiver(user_signals.service_created)
def service_created_track(sender, user, request, response, **kwargs):
    event = constants.SERVICES_CREATION
    analytics_track_properties=response.data
    analytics_track(user, event, analytics_track_properties)


@receiver(user_signals.phone_number_verified)
def phone_number_verified_track(sender, user, request, **kwargs):
    event = constants.PHONE_NUMBER_VERIFIED
    analytics_track_properties = {
        "phone": str(request.user.new_phone_number)
    }
    analytics_track(user, event, analytics_track_properties)


# TODO CREATE SIGNAL AT VIEW LEVEL
@receiver(post_signals.post_created)
def post_created_track(sender, user, post, **kwargs):
    event = constants.POST_CREATED
    analytics_track_properties = {
        "message": post.message,
        "post_id": post.pk
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(user_signals.referred_friend)
def referred_friend_track(sender, user, request, **kwargs):
    event = constants.REFERRED_FRIEND
    analytics_track_properties = {
        "referal_email":  request.data.get("email").strip(),
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(meetings_signals.registered_for_meeting)
def registered_for_meeting_track(sender, user, **kwargs):
    # Removing signal object from kwargs.
    kwargs.pop("signal")

    created = kwargs.pop("created", None)
    event = constants.REGISTERED_MEETING_PREFERENCES if created else constants.EDIT_MEETING_PREFERENCES

    analytics_track_properties = kwargs

    analytics_track(user, event, analytics_track_properties)


@receiver(meetings_signals.new_meeting_config_created)
def new_meeting_config_created_track(sender, user, **kwargs):
    # Removing signal object from kwargs.
    kwargs.pop("signal")

    event = constants.MEETING_CONFIG_CREATED
    analytics_track_properties = kwargs

    analytics_track(user, event, analytics_track_properties)


@receiver(meetings_signals.new_meeting_created)
def new_meeting_created_track(sender, user, **kwargs):
    """Sending new meeting creations to Analytics."""
    kwargs.pop("signal")

    event = constants.MEETING_CREATED
    analytics_track_properties = kwargs

    analytics_track(user, event, analytics_track_properties)


@receiver(creative_exchange_signals.request_created)
def creative_exchange_request_created_track(sender, user, **kwargs):
    """Sending new Creative Exchange Request to Analytics."""
    kwargs.pop("signal")

    event = constants.CREATIVE_EXCHANGE_REQUEST_CREATED
    analytics_track_properties = kwargs

    analytics_track(user, event, analytics_track_properties)


@receiver(meetings_signals.rsvp_status_updated)
def meeting_rsvp_updated(sender, user, rsvp, *args, **kwargs):
    """Sending meeting RSVP to Analytics."""
    kwargs.pop("signal")

    event = constants.RSVP_UPDATED
    analytics_track_properties = {
        "meeting_id": rsvp.meeting.id,
        "participant": rsvp.participant.email,
        "status": rsvp.status,
        "meeting_config": rsvp.meeting.config.id,
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(meetings_signals.reschedule_request_created)
def reschedule_request_created(sender, reschedule_request, *args, **kwargs):
    """When a reschedule request is created, send analytics."""
    event = constants.RESCHEDULE_CREATED
    analytics_track_properties = {
        "id": reschedule_request.pk,
        "meeting_id": reschedule_request.old_meeting.id,
        "creator": reschedule_request.requested_by.email,
        "approver": reschedule_request.approver.email,
        "status": reschedule_request.status,
    }
    analytics_track(user=reschedule_request.requested_by, event=event, analytics_track_properties=analytics_track_properties)


@receiver(meetings_signals.reschedule_request_approved)
def reschedule_request_approved(sender, reschedule_request, *args, **kwargs):
    """When a reschedule request is updated, send analytics."""
    event = constants.RESCHEDULE_UPDATED
    analytics_track_properties = {
        "id": reschedule_request.pk,
        "meeting_id": reschedule_request.old_meeting.id,
        "new_meeting_id": reschedule_request.new_meeting.id,
        "creator": reschedule_request.requested_by.email,
        "status": reschedule_request.status,
        "approver": reschedule_request.approver.email,
        "selected_slot": reschedule_request.new_meeting.get_display()
    }
    analytics_track(user=reschedule_request.approver, event=event, analytics_track_properties=analytics_track_properties)


@receiver(meetings_signals.reschedule_request_declined)
def reschedule_request_declined(sender, reschedule_request, *args, **kwargs):
    """When a reschedule request is updated, send analytics."""
    event = constants.RESCHEDULE_UPDATED
    analytics_track_properties = {
        "id": reschedule_request.pk,
        "meeting_id": reschedule_request.old_meeting.id,
        "creator": reschedule_request.requested_by.email,
        "approver": reschedule_request.approver.email,
        "status": reschedule_request.status,
    }
    analytics_track(user=reschedule_request.approver, event=event, analytics_track_properties=analytics_track_properties)


@receiver(conversation_signals.conversation_created)
def conversation_created(sender, group, *args, **kwargs):
    event = constants.CONVERSATION_CREATED

    # Sending the event once for every email.
    for user in group.speakers.all():
        analytics_track_properties = {
            "id": group.id,
            "host": group.host.email if group.host else None,
            "speakers": list(group.speakers.all().values_list("email", flat=True)),
            "topic": group.topic.name,
            "start": group.get_display()
        }
        analytics_track(
            user=user,
            event=event,
            analytics_track_properties=analytics_track_properties
        )


@receiver(conversation_signals.user_joined_group)
def conversation_joined(sender, user, group, *args, **kwargs):
    """Sending an event when user joined """
    event = constants.CONVERSATION_JOINED

    analytics_track_properties = {
        "id": group.id,
        "host": group.host.email if group.host else None,
        "speakers": list(group.speakers.all().values_list("email", flat=True)),
        "topic": group.topic.name,
        "start": group.get_display()
    }
    analytics_track(
        user=user,
        event=event,
        analytics_track_properties=analytics_track_properties
    )


def _add_user_device_info(user, analytics_track_properties):
    device_info = user.device_info.first()
    if not device_info:
        return

    analytics_track_properties["os"] = device_info.get_os_info()
    analytics_track_properties["devices"] = device_info.get_device_info()
    analytics_track_properties["device_type"] = device_info.type

    return
