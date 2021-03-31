from django.dispatch import Signal

user_joined_group = Signal(providing_args=[
    "group", "user"
])
