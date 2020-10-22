from django.utils.translation import ugettext_lazy as _

MESSAGE_EMAIL_NOTIFICATION_STATE = (
    ('Scheduled', _('Scheduled')),
    ('Pending', _('Pending')),
    ('Revoked', _('Revoked')),
    ('Sent', _('Sent')),
)

CHAT_EMAIL_TEMPLATE = 'Chat Message Notification'

MESSAGE_NOTIFICATION_FROM_EMAIL = 'messages@worknetwork.in'
