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