from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from resources.events.models import RSVPD
from resources.events.tasks import send_email


@receiver(post_save, sender=RSVPD)
def send_rsvpd_email(sender, instance, **kwargs):
    """
    Send email after subscribing for event
    :param sender: Subscribing for event mode
    :param instance: Subscribing for event instance
    :param kwargs: Additional params
    :return: None
    """
    # TODO Send email for instance.user.email (using SMTP)
    message = _('You are invited to the event on {} at {}').format(instance.event.date, instance.event.start)
    send_email.delay(instance.event.title, message, 'from@example.com', instance.user.email)
