from django.dispatch import Signal

sale_payment_confirmed = Signal(providing_args=["sale_log"])
