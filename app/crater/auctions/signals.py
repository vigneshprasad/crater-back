from django.dispatch import Signal

bid_placed = Signal(providing_args=["bid"])
bid_payment_charge_capture_setup = Signal(providing_args=["bid"])
bid_payment_charge_capture_success = Signal(providing_args=["bid"])
