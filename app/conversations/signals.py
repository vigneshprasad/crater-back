from django.dispatch import Signal

user_joined_group = Signal(providing_args=[
    "group", "user"
])

new_conversation_registration = Signal(providing_args=[
    "preference"
])

conversation_created = Signal(providing_args=[
    "group"
])

conversation_approved = Signal(providing_args=[
    "group"
])

webinar_created = Signal(providing_args=[
    "group"
])

group_marked_live = Signal(providing_args=[
    "group"
])

group_marked_inactive = Signal(providing_args=[
    "group"
])

group_marked_closed = Signal(providing_args=[
    "group"
])

attendee_added_to_group = Signal(providing_args=[
    "group",
    "user"
])

# This is used when multiple attendees are added at the same
# time.
attendees_added_to_group = Signal(providing_args=[
    "group",
    "users"
])

speaker_added_to_group = Signal(providing_args=[
    "group",
    "users"
])

speakers_added_to_webinar = Signal(providing_args=[
    "group",
    "speakers"
])
