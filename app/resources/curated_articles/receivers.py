from django.db.models.signals import post_save
from django.dispatch import receiver

from resources.curated_articles import models
from resources.curated_articles import signals


@receiver(post_save, sender=models.CuratedArticle)
def article_post_save(sender, instance,  created, *args, **kwargs):
    """Sends article updated or created signals for other apps to listen to.

    Args:
        sender(CuratedArticle.__class__): Sender for the post save event.
        instance(CuratedArticle): Instance of CuratedArticle created or updated.
        created(Boolean): True if CuratedArticle is created, else False.

    """
    if created:
        signals.curated_article_created(sender=models.CuratedArticle.__class__, article=instance)

    signals.curated_article_updated(sender=models.CuratedArticle.__class__, article=instance)
