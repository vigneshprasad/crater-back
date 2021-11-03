import random
import string
from django.utils.text import slugify


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_unique_slug_for_creator(instance, new_slug=None):
    if new_slug is not None:
        slug = new_slug
    else:
        str = instance.user.name.lower()
        slug = slugify(str)

    Klass = instance.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()

    if qs_exists:
        new_slug = "{slug}-{randstr}".format(
            slug=slug,
            randstr=random_string_generator(size=4)
        )
        return generate_unique_slug_for_creator(instance, new_slug=new_slug)
    return slug
