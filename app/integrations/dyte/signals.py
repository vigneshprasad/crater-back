from django.dispatch import Signal

new_recording_started = Signal(providing_args=[
    "dyte_recording"
])
