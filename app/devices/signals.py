from django.dispatch import Signal

new_user_device_detected = Signal(providing_args=[
    "user", "device_name", "device_model", "device_price"
])
