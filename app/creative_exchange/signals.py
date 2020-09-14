from django.dispatch import Signal

request_created = Signal(providing_args=[
    "user",
])