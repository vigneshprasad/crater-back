import base64
import binascii
from mimetypes import guess_extension, guess_type

import six
from django.core.files.base import ContentFile
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class Base64FileField(serializers.FileField):
    ext_mapping = {
        '.jpe': '.jpg'
    }
    file_formats = []
    default_error_messages = {
        'invalid_file': _('File format is invalid.'),
        'wrong_file_format': _('Wrong file format')
    }

    def __init__(self, *args, **kwargs):
        self.file_formats = kwargs.pop('file_formats', [])
        super().__init__(*args, **kwargs)

    def to_internal_value(self, payload):
        if isinstance(payload, six.string_types):
            file_extension = None
            try:
                data = None
                if 'data:' in payload and ';base64,' in payload:
                    header, data = payload.split(';base64,')
                    file_extension = guess_extension(guess_type(f'{header};base64,')[0])
                    file_extension = self.ext_mapping.get(file_extension, file_extension)
                    if self.file_formats and file_extension not in self.file_formats:
                        self.fail('wrong_file_format')
                try:
                    decoded_file = base64.b64decode(data)
                except (TypeError, binascii.Error):
                    self.fail('invalid_file')

                complete_file_name = f'freelance_file{file_extension}'
                data = ContentFile(decoded_file, name=complete_file_name)
            except IndexError:
                data = None
            return super().to_internal_value(data)
