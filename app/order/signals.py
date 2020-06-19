from django.dispatch import Signal

service_complete_seller_points_signal = Signal(providing_args=[
  "user",
  "rule_key",
  "base_factor"
])

service_complete_buyer_points_signal = Signal(providing_args=[
  "user",
  "rule_key",
  "base_factor"
])