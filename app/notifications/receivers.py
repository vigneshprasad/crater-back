from django.contrib.auth import get_user_model
from django.dispatch import receiver

from notifications import models
from resources.curated_articles import signals as article_signals


@receiver(article_signals.curated_article_created)
def article_post_save(sender, article, *args, **kwargs):
    """Create notifications on Article creation.

    Args:
        sender(CuratedArticle.__class__): Sender for the post save event.
        article(CuratedArticle): Instance of CuratedArticle created or updated.

    """
    notification = models.Notification.objects.create(article=article)
    users = get_user_model().objects.filter(profile__isnull=False)
    for user in users:
        models.UserNotification.objects.create(user=user, notification=notification)
