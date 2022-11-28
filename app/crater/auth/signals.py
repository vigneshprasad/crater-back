from django.dispatch import Signal

new_user_signal = Signal(providing_args=["user"])
