from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from conversations import constants
from conversations import models
from matching import private as matching_private
from resources.meetings import signals as meeting_signals
from resources.curated_articles import signals as article_signals


@receiver(m2m_changed, sender=models.Group.speakers.through)
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
