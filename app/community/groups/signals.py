from django.dispatch import Signal

follower_recieved_signal = Signal(providing_args=[
    "user",
    "rule_key",
    "base_factor"
])