from django.dispatch import Signal


user_created = Signal(providing_args=[
    "user",
])

user_updated = Signal(providing_args=[
    "user",
])

user_signed_up = Signal(providing_args=[
    "user",
])

user_name_populated = Signal(providing_args=[
    "user"
])

objectives_added = Signal(providing_args=[
    "user",
    "objectives",
])

email_verified = Signal(providing_args=[
    "user",
])

basic_profile_created = Signal(providing_args=[
    "user",
    "request",   
    "response" 
])

phone_number_verified = Signal(providing_args=[
    "user",
    "request"
])

service_created = Signal(providing_args=[
    "user",
    "request",
    "response"
])

referred_friend = Signal(providing_args=[
    "user",
    "request",    
])

profile_completed = Signal(providing_args=[
    "rule_key",
    "user",
])

referal_success_points_signal = Signal(providing_args=[
    "rule_key",
    "user",
])

profile_requested = Signal(providing_args=[
    "profile"
])

user_logout = Signal(providing_args=[
    "user",
    "os_id",
])
