from django.dispatch import receiver
from .models import TrackLog, IdentifyLog
from community.posts.signals import post_created
from resources.meetings import signals as meetings_signals
from users.models import User
from users.signals import basic_profile_created, user_signed_up, service_created, phone_number_verified, user_updated, agreement_filled, referred_friend, email_verified
from utils.segment_service import segment_service
from wn_analytics.constants import *
from wn_analytics.utils import get_user_traits


def analytics_track(user, event, analytics_track_properties={}):
    user_id = str(user.pk)
    # TODO(Nishant): Will reuse this code when Flutter app is released.
    # Added user device info to the track properties.
    # _add_user_device_info(user, analytics_track_properties)

    segment_service.track(
        user_id=user_id, 
        event=event,
        properties=analytics_track_properties
    )
    TrackLog.objects.create(
        user=user,
        event=event,
        properties=analytics_track_properties
    )


@receiver(user_updated)
def analytics_identify(sender, user, **kwargs):
    user_id = str(user.pk)
    traits = get_user_traits(user)

    segment_service.identify(
        user_id=user_id, 
        traits=traits
    )
    IdentifyLog.objects.create(
        user=user,
        traits=traits
    )


@receiver(user_signed_up)
def user_signed_up_track(sender, user, **kwargs):
    event=USER_CREATED
    analytics_track_properties={
        'email': user.email, 
        'role': user.role,
        'name': user.name,
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(email_verified)
def email_verified_track(sender, email_address, **kwargs):
    event=EMAIL_VERIFIED
    user = User.objects.get(email=email_address.email)
    analytics_track_properties={
        'email': email_address.email, 
        'role': user.role,
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(agreement_filled)
def agreement_filled_track(sender, user, **kwargs):
    event=AGREEMENT_FILLED
    analytics_track_properties={
        'city': str(user.city),
        'email': user.email,
        'role': user.role
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(basic_profile_created)
def basic_profile_track(sender, user, request, response, **kwargs):
    analytics_track_properties = {}
    analytics_track_properties['name'] = response.data['name']
    analytics_track_properties['focus'] = response.data['focus']
    analytics_track_properties['introduction'] = response.data['introduction']
    analytics_track_properties['tag_line'] = response.data['tag_line']
    analytics_track_properties['twitter'] = response.data['twitter']
    analytics_track_properties['instagram_id'] = response.data['instagram_id']
    analytics_track_properties['additional_information'] = response.data['additional_information']
    analytics_track_properties['photo'] = response.data['photo']
    analytics_track_properties['work_city'] = response.data['work_city_name']
    tag_list = response.data['tag_list']
    tags = []
    for tag in tag_list:
        tags.append(tag['name'])
    analytics_track_properties['tags'] = tags
    event=BASIC_PROFILE_CREATED
    analytics_track(user, event, analytics_track_properties)


@receiver(service_created)
def service_created_track(sender, user, request, response, **kwargs):
    event=SERVICES_CREATION
    analytics_track_properties=response.data
    analytics_track(user, event, analytics_track_properties)


@receiver(phone_number_verified)
def phone_number_verified_track(sender, user, request, **kwargs):
    event=PHONE_NUMBER_VERIFIED
    analytics_track_properties={
        'phone': str(request.user.new_phone_number)
    }
    analytics_track(user, event, analytics_track_properties)


# TODO CREATE SIGNAL AT VIEW LEVEL
@receiver(post_created)
def post_created_track(sender, user, post, **kwargs):
    event=POST_CREATED
    analytics_track_properties={
        'message': post.message,
        'post_id': post.pk
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(referred_friend)
def referred_friend_track(sender, user, request, **kwargs):
    event=REFERRED_FRIEND
    analytics_track_properties = {
        'referal_email':  request.data.get('email').strip(),
    }
    analytics_track(user, event, analytics_track_properties)


@receiver(meetings_signals.registered_for_meeting)
def registered_for_meeting_track(sender, user, **kwargs):
    # Removing signal object from kwargs.
    kwargs.pop('signal')

    created = kwargs.pop('created', None)
    event = REGISTERED_MEETING_PREFERENCES if created else EDIT_MEETING_PREFERENCES

    analytics_track_properties = kwargs

    analytics_track(user, event, analytics_track_properties)


@receiver(meetings_signals.new_meeting_config_created)
def new_meeting_config_created_track(sender, user, **kwargs):
    # Removing signal object from kwargs.
    kwargs.pop('signal')

    event = MEETING_CONFIG_CREATED
    analytics_track_properties = kwargs

    analytics_track(user, event, analytics_track_properties)


def _add_user_device_info(user, analytics_track_properties):
    device_info = user.device_info.first()
    if not device_info:
        return

    analytics_track_properties['os'] = device_info.get_os_info()
    analytics_track_properties['device'] = device_info.get_device_info()
    analytics_track_properties['device_type'] = device_info.type

    return
