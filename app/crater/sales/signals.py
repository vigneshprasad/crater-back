from django.dispatch import Signal

sale_payment_confirmed = Signal(providing_args=["sale_log"])
sale_payment_declined = Signal(providing_args=["sale_log"])
sale_created = Signal(providing_args=["sale_log"])

reward_sale_quantity_updated = Signal(providing_args=["reward_sale"])
