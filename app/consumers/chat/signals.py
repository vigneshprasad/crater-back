from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

from consumers.chat.helpers import MessageHelper
from consumers.chat.models import Message


new_chat_points_signal = Signal(providing_args=[
    "user",
    "rule_key",
    "base_factor"
])

create_chat_for_meeting = Signal(providing_args=[
    "participants",
])
