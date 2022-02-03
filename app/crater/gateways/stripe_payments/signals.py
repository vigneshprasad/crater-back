from django.dispatch import Signal

capture_payment_intent_success = Signal(providing_args=["intent", "bidder", "bid"])
