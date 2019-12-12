from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def file_size(value, size=512):
    message = _('File too large. Size should not exceed {} MiB.')
    limit = size * 1024 * 1024
    if value.size > limit:
        raise ValidationError(message.format(size))


def file_size_wrap(size):
    def file_size(value):
        message = _('File too large. Size should not exceed {} MiB.')
        limit = size * 1024 * 1024
        if value.size > limit:
            raise ValidationError(message.format(size))
    return file_size
