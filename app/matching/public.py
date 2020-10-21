from itertools import islice

from matching import private
from resources.meetings import services as meeting_service


def get_top_matches_for_user(user):
    """Returns top 10 matches for a user."""
    opted_in_users = meeting_service.get_opted_in_user_for_meetings()
    user_match_score_map = {}

    for opted_user in opted_in_users:
        match_score = private.get_match_score_between_users(user, opted_user)
        user_match_score_map[user.email] = match_score

    # Sorting the user match score.
    sorted_user_match_score_map = {k: v for k, v in sorted(a.items(), key=lambda item: item[1])}
    # Return top 10 users.
    return dict(islice(sorted_user_match_score_map.items(), 10))
