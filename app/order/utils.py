from .signals import service_complete_seller_points_signal, service_complete_buyer_points_signal

SERVICE_COMPLETE_BUYER_POINTS_KEY = 11
SERVICE_COMPLETE_SELLER_POINTS_KEY = 12

def send_service_complete_seller_points_signal(order, seller, **kwargs):
  service_complete_seller_points_signal.send(
    sender=order.__class__,
    user=seller,
    rule_key=SERVICE_COMPLETE_SELLER_POINTS_KEY
  )

def send_service_complete_buyer_points_signal(order, buyer, **kwargs):
  service_complete_seller_points_signal.send(
    sender=order.__class__,
    user=buyer,
    rule_key=SERVICE_COMPLETE_BUYER_POINTS_KEY
  )