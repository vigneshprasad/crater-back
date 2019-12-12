import base64
import binascii

import six

from django.utils.translation import ugettext_lazy as _
from mimetypes import guess_extension, guess_type
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64FileField(serializers.FileField):
    ext_mapping = {
        '.jpe': '.jpg'
    }
    default_error_messages = {
        'invalid_file': _('File format is invalid.'),
    }

    def to_internal_value(self, payload):
        if isinstance(payload, six.string_types):
            file_extension = None
            try:
                data = None
                if 'data:' in payload and ';base64,' in payload:
                    header, data = payload.split(';base64,')
                    file_extension = guess_extension(guess_type(f'{header};base64,')[0])
                    file_extension = self.ext_mapping.get(file_extension, file_extension)
                try:
                    decoded_file = base64.b64decode(data)
                except (TypeError, binascii.Error):
                    self.fail('invalid_file')

                complete_file_name = f'freelance_file{file_extension}'
                data = ContentFile(decoded_file, name=complete_file_name)
            except IndexError:
                data = None
            return super().to_internal_value(data)
