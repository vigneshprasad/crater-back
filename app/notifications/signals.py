from django.dispatch import Signal

app_started_signal = Signal(providing_args=[
    "user",
    "device_info",
])
