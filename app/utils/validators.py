from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.deconstruct import deconstructible


@deconstructible
class SizeValidator(object):
    def __init__(self, **params):
        self._size = params.get('size', 512)

    def __call__(self, value):
        message = _('File too large. Size should not exceed {} MiB.')
        limit = self._size * 1024 * 1024
        if value.size > limit:
            raise ValidationError(message.format(self._size))
        else:
            return value
