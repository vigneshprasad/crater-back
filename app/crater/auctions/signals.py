from django.dispatch import Signal

bid_placed = Signal(providing_args=["bid"])
