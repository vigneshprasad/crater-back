import random
import string
from django.utils.text import slugify


def random_string_generator(size=10, chars=string.ascii_lowercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def generate_unique_slug_for_creator(creator, new_slug=None):
    """Generate a unique slug for a creator."""

    slug = new_slug if new_slug is not None else slugify(creator.user.name.lower())

    Klass = creator.__class__
    qs_exists = Klass.objects.filter(slug=slug).exists()
    if not qs_exists:
        return slug

    new_slug = "{slug}-{random_str}".format(
        slug=slug,
        random_str=random_string_generator(size=4)
    )

    # Generate a unique slug again.
    return generate_unique_slug_for_creator(
        creator, new_slug=new_slug
    )
