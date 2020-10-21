from itertools import islice

from django.contrib.auth import get_user_model

from matching import private, private2
from resources.meetings import services as meeting_service


def get_top_matches(user):
    """Returns top 10 matches for a user taking into account the other users preferences."""
    opted_in_users = meeting_service.get_opted_in_user_for_meetings()
    user_match_score_map = {}

    for opted_user in opted_in_users:
        if not opted_user.has_profile:
            continue
        match_score = private.get_match_score_between_users(user, opted_user)
        user_match_score_map[opted_user.email] = match_score

    # Removing user's match with the user itself.
    user_match_score_map.pop(user.email)

    # Sorting the user match score.
    sorted_user_match_score_map = {k: v for k, v in sorted(
        user_match_score_map.items(), key=lambda item: item[1], reverse=True
    )}
    # Return top 10 users.
    final_results = dict(islice(sorted_user_match_score_map.items(), 10))
    print("User Info")
    private.get_user_info(user)
    for email, score in final_results.items():
        print('Start', '*'*30)
        matched_user = get_user_model().objects.get(email=email)
        print('Match Score: {}'.format(score))
        private.get_user_info(matched_user)
        print('End', '*' * 30)

    return dict(islice(sorted_user_match_score_map.items(), 10))


def get_top_matches_for_user(user):
    """Returns top 10 matches for a user without taking into account the other users preferences."""
    opted_in_users = meeting_service.get_opted_in_user_for_meetings()
    user_match_score_map = {}

    for opted_user in opted_in_users:
        if not opted_user.has_profile:
            continue
        match_score = private2.get_match_score_between_users(user, opted_user)
        user_match_score_map[opted_user.email] = match_score

    # Removing user's match with the user itself.
    user_match_score_map.pop(user.email)

    # Sorting the user match score.
    sorted_user_match_score_map = {k: v for k, v in sorted(
        user_match_score_map.items(), key=lambda item: item[1], reverse=True
    )}
    # Return top 10 users.
    final_results = dict(islice(sorted_user_match_score_map.items(), 10))
    print("User Info")
    private.get_user_info(user)
    for email, score in final_results.items():
        print('Start', '*'*30)
        matched_user = get_user_model().objects.get(email=email)
        print('Match Score: {}'.format(score))
        private.get_user_info(matched_user)
        print('End', '*' * 30)

    return dict(islice(sorted_user_match_score_map.items(), 10))
