from django.dispatch import Signal

creator_followed = Signal(providing_args=["follower"])
creator_unfollowed = Signal(providing_args=["follower"])
