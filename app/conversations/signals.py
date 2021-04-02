from django.dispatch import Signal

user_joined_group = Signal(providing_args=[
    "group", "user"
])

new_conversation_registration = Signal(providing_args=[
    "preference"
])
