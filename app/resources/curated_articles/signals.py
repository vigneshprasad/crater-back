from django.dispatch import Signal

curated_article_created = Signal(providing_args=[
    "article"
])

curated_article_updated = Signal(providing_args=[
    "article"
])

