from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from resources.events.models import RSVPD
from users import choices
from users.tasks import send_email


@receiver(post_save, sender=RSVPD)
def send_rsvpd_email(sender, instance, **kwargs):
    """
    Send email after subscribing for event
    :param sender: Subscribing for event mode
    :param instance: Subscribing for event instance
    :param kwargs: Additional params
    :return: None
    """
    email = instance.user.email
    data = {
        email: {
            'date': str(instance.event.date),
            'time': str(instance.event.start),
            'user': str(instance.user)
        }
    }
    send_email.delay(
        subject=_('Event invitation'),
        to=[email],
        template_name=choices.template_names.get('participate_event'),
        content={},
        merge_vars=data
    )
