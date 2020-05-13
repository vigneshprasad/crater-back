from django.contrib import admin
from django.utils import timezone
from django.utils import translation


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


def translate(language, text):
    lang = translation.get_language()
    translation.activate(language)
    text = translation.ugettext(text)
    translation.activate(lang)
    return text


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timezone.timedelta(n)
