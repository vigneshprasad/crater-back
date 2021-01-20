from django.dispatch import Signal

registered_for_meeting = Signal(providing_args=[
    "user",
    "week_start_date",
    "week_end_date",
    "created",
    "interests",
    "objectives",
    "number_of_meetings",
    "time_slots",
    "meeting"
])

new_meeting_registration = Signal(providing_args=[
    "preference"
])

new_meeting_config_created = Signal(providing_args=[
    "user",
    "week_start_date",
    "week_end_date",
    "title",
    "registration_start_date",
    "registration_end_date",
    "time_slots",
])

create_new_meeting_preference_typeform = Signal(providing_args=[
    "user",
    "time_preferences",
    "interests",
    "objectives",
    "days"
])

new_meeting_created = Signal([
    "user",
    "time_slot",
    "participants",
    "meeting_config",
    "meeting_link"
])

new_user_assigned_to_meeting = Signal(providing_args=[
    "user",
    "rule_key",
    "base_factor"
])

rsvp_status_updated = Signal(providing_args=[
    "user",
    "rsvp"
])

reschedule_request_approved = Signal(providing_args=[
    "reschedule_request"
])

reschedule_request_declined = Signal(providing_args=[
    "reschedule_request",
])

meeting_marked_cancelled = Signal(providing_args=[
    "meeting"
])

reschedule_request_created = Signal(providing_args=[
    "reschedule_request"
])
