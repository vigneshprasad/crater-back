import logging
from django.contrib.auth import get_user_model
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from conversations import constants, models, signals, services
from integrations.dyte import tasks as dyte_tasks, public as dyte_public, signals as dyte_signals
from matching import private as matching_private
from resources.curated_articles import signals as article_signals
from resources.meetings import signals as meeting_signals
from crater.sales import signals as sales_signals
from crater.rewards import constants as reward_constants


@receiver(post_save, sender=models.Group)
def send_webinar_creation_signal(sender, instance, *args, **kwargs):
    """Send webinar creation signal on Group post save

    Note:
        Don't send the signal if the group is being updated.

    """
    if not (instance.type == constants.GROUP_TYPE_WEBINAR_ENUM):
        return

    if dyte_public.get_dyte_webinar_for_group(instance):
        return

    signals.webinar_created.send(sender=instance.__class__, group=instance)


# @receiver(signals.group_marked_live)
# def create_webinar_cache(sender, group, *args, **kwargs):
#     services.cache_live_webinar(group=group)


# @receiver(signals.group_marked_closed)
# def remove_webinar_cache(sender, group, *args, **kwargs):
#     services.remove_cached_live_webinar(group=group)


@receiver(signals.group_marked_closed)
def recalculate_minutes_for_group(sender, group, *args, **kwargs):
    """Recalculate minutes for a group once it's marked closed.

    Args:
        sender(Group.__class__): Class representation of group.
        group(Group): Group that was just marked closed.

    """
    dyte_tasks.recalculate_minutes_for_groups([group.id])


@receiver(signals.group_marked_closed)
def mark_all_dyte_participants_offline(sender, group, *args, **kwargs):
    """Mark all dyte participants offline for a group once
        it's marked closed.

    Args:
        sender(Group.__class__): Class representation of group.
        group(Group): Group that was just marked closed.

    """
    dyte_tasks.mark_dyte_meeting_participants_offline.apply_async(
        args=(group.id, ),
        countdown=120
    )


# @receiver(m2m_changed, sender=models.Group.speakers.through)
def update_group_score(sender, instance, *args, **kwargs):
    """Update group score as a user is removed or added to the group."""
    if kwargs.get("action") not in ["post_add", "post_remove"]:
        return

    if not instance.calculate_score:
        return

    speakers = instance.speakers.all()
    score = matching_private.calculate_average_group_score_based_on_user_score(speakers)

    instance.score = score
    instance.save()


@receiver(m2m_changed, sender=models.Group.speakers.through)
def change_group_occupancy_status(sender, instance, *args, **kwargs):
    """Update group is_full as a user is removed or added to the group."""
    if kwargs.get("action") not in ["post_add", "post_remove"]:
        return

    speakers_count = instance.speakers.count()

    if constants.DEFAULT_MAX_SPEAKERS > speakers_count:
        instance.is_full = False
        instance.save()
        return

    instance.is_full = True
    instance.save()


@receiver(m2m_changed, sender=models.Group.speakers.through)
def create_calendar_add_dyte_participant_for_new_speakers(sender, instance, *args, **kwargs):
    """Create calendar when a new speaker is added"""
    if kwargs.get("action") not in ["post_add"]:
        return

    if not instance.type == constants.GROUP_TYPE_WEBINAR_ENUM:
        return

    if not instance.host:
        return

    speaker_ids = kwargs.get("pk_set")

    speakers = get_user_model().objects.filter(pk__in=speaker_ids).exclude(pk=instance.host.pk)

    signals.speakers_added_to_webinar.send(
        sender=instance.__class__,
        group=instance,
        speakers=speakers
    )
    

@receiver(meeting_signals.new_meeting_registration)
def update_topic_for_meeting_preference(sender, preference, *args, **kwargs):
    """Updates preference topic given objectives."""

    # Preference object already has a topic.
    if preference.topic:
        return

    objectives = preference.objectives.all()
    topic_names = []

    for objective in objectives:
        topic_name = constants.OBJECTIVE_TO_TOPIC_MAP.get(objective.name)
        if not topic_name:
            continue
        topic_names.append(topic_name)

    topic = models.Topic.objects.filter(name__in=topic_names).first()

    if not topic:
        # Doing a filter in case Default topic is not present on the environment.
        topic = models.Topic.objects.filter(name=constants.DEFAULT_TOPIC_NAME).first()

    preference.topic = topic
    preference.save()


@receiver(article_signals.curated_article_created)
@receiver(article_signals.curated_article_updated)
def create_topic_for_article(sender, article, *args, **kwargs):
    """Create topic from articles.

    Args:
        sender(CuratedArticle.__class__): Sender for the post save event.
        article(CuratedArticle): Instance of CuratedArticle created or updated.

    """
    if not article.is_topic:
        return

    parent_topic = models.Topic.objects.filter(name="Other").first()

    # Update or create a topic for the article.
    topic, _ = models.Topic.objects.update_or_create(
        article=article,
        defaults={
            "name": article.title,
            "image": article.image,
            "parent": parent_topic,
            "description": article.description,
            "is_active": False
        }
    )

    return topic


@receiver(dyte_signals.new_recording_started)
def create_or_update_group_recording(sender, dyte_recording, *args, **kwargs):
    """Creates or updates group recording for a new dyte recording started.

    Args:
        sender(dyte.DyteMeetingRecording class): Dyte recording object class.
        dyte_recording(dyte.DyteMeetingRecording): Dyte recording that was just
            started.

    """
    group = dyte_recording.dyte_meeting.group
    if not group:
        return

    try:
        group_recording = group.recording
    except models.GroupRecording.DoesNotExist:
        group_recording = None

    if not group_recording:
        # If there is no group recording for the group
        # create one.
        group_recording = models.GroupRecording.objects.create(
            group=group
        )
        group_recording.dyte_recordings.add(dyte_recording)

        return group_recording

    # Updating the existing group recording if the object is
    # present for the group.
    group_recording.dyte_recordings.add(dyte_recording)

    return group_recording

@receiver(sales_signals.sale_payment_confirmed)
def add_attendee_for_private_stream_sale_confirmation(sender, sale_log, *args, **kwargs):
    """

    """
    reward = sale_log.reward_sale.reward
    if not reward.type.name == reward_constants.REWARD_NAME_PRIVATE_STREAM:
        return

    if not reward.object_id:
        return
    
    try:
        group = models.Group.objects.get(id=reward.object_id)
    except models.Group.DoesNotExist:
        logging.error("Reward group does not exist for private stream", reward.id)
        return

    request = services.create_group_request(user=sale_log.user, group=group, participant_type=constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM)
    services.add_attendee_to_group_for_request(attendee=sale_log.user, group_request=request)
