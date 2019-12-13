from django.db.models.signals import post_save
from django.dispatch import receiver

from resources.events.models import RSVPD


@receiver(post_save, sender=RSVPD)
def send_rsvpd_email(sender, instance, **kwargs):
    """
    Send email after subscribing for event
    :param sender: Subscribing for event mode
    :param instance: Subscribing for event instance
    :param kwargs: Additional params
    :return: None
    """
    # TODO Send email for instance.user.email
    print(instance.user.email)
