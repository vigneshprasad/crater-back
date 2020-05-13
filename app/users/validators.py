from rest_framework import exceptions
import re
from django.utils.translation import ugettext_lazy as _


def password_validate_symbols(password):
    if not re.search("[0-9]", password) or not re.search("[A-Za-z]", password):
        raise exceptions.ValidationError(_('Password should contain numbers and letters'))

