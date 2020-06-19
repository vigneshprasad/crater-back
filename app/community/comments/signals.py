from django.dispatch import Signal

comment_created_points = Signal(providing_args=[
    "user",
    "rule_key"
])

comment_created_post_author_points = Signal(providing_args=[
    "user",
    "rule_key"
])