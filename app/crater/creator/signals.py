from django.dispatch import Signal

creator_followed = Signal(providing_args=["follower"])
creator_unfollowed = Signal(providing_args=["follower"])
user_added_to_community = Signal(providing_args=["community_member"])
creator_50_subscribers = Signal(providing_args=["creator"])
analytics_enabled_for_creator = Signal(providing_args=["creator"])
