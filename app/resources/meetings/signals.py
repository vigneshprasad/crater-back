from django.dispatch import Signal

registered_for_meeting = Signal(providing_args=[
    "user",
    "week_start_date",
    "week_end_date",
    "created",
    "interests",
    "objective",
    "number_of_meetings",
    "time_slots",
    "meeting"
])

new_meeting_created = Signal(providing_args=[
    "user",
    "week_start_date",
    "week_end_date",
    "title",
    "registration_start_date",
    "registration_end_date",
    "time_slots",
])
