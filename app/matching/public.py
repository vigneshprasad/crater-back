from itertools import islice

from django.contrib.auth import get_user_model

from matching import constants
from matching.engines import user_match_engine
from matching.engines import best_match_engine
from matching.engines import users_scoring
from resources.meetings import services as meeting_service


def get_top_matches_for_user(user):
    """Returns top 10 matches for a user taking into account the other users preferences.

    Note:
        This function will give preference to the match score between user i.e how good
            the match will be between two users. So it's average score for two users who are
            being matched.

    """
    # user_score = users_scoring.get_user_score(user)
    opted_in_users = meeting_service.get_opted_in_user_for_meetings()
    user_match_score_map = {}

    for opted_user in opted_in_users:
        if not opted_user.has_profile:
            continue

        final_score, detailed_score = user_match_engine.get_match_score_between_users(user, opted_user)
        # opted_user_score = users_scoring.get_user_score(opted_user)

        user_match_score_map[opted_user.email] = [final_score, detailed_score]

    # Removing user's match with the user itself.
    try:
        user_match_score_map.pop(user.email)
    except KeyError:
        pass

    # Sorting the user match score.
    sorted_user_match_score_map = {k: v for k, v in sorted(
        user_match_score_map.items(), key=lambda item: item[1], reverse=True
    )}

    # Return top 10 users.
    results = dict(islice(sorted_user_match_score_map.items(), 10))
    final_results = []
    for email, score_list in results.items():
        matched_user = get_user_model().objects.get(email=email)
        data = {
            "email": email,
            "user_id": matched_user.pk,
            "match_score": score_list[0],
            # These are detailed score details.
            constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE: score_list[1].get(constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE),
            constants.TAG_TO_TAG_ENGINE: score_list[1].get(constants.TAG_TO_TAG_ENGINE),
            constants.OBJECTIVE_TO_OBJECTIVE_ENGINE: score_list[1].get(constants.OBJECTIVE_TO_OBJECTIVE_ENGINE),
            constants.INTRODUCTION_TEXT_ENGINE: score_list[1].get(constants.INTRODUCTION_TEXT_ENGINE),
            constants.SECTOR_MATCH_ENGINE: score_list[1].get(constants.SECTOR_MATCH_ENGINE)
        }
        final_results.append(data)

    return final_results


def get_top_users_for_user(user):
    """Returns top 10 matches for a user based on only his preferences.

    Note:
        This function only calculates the score based on only the given user's
            preferences, i.e it doesn't mean the other user should be matched
            with the the given user. It means he might be an ideal match, but the
            other user might want to meet someone else based on his preferences.

    """
    # user_score = users_scoring.get_user_score(user)
    opted_in_users = meeting_service.get_opted_in_user_for_meetings()
    user_match_score_map = {}

    for opted_user in opted_in_users:
        if not opted_user.has_profile:
            continue

        final_score, detailed_score = best_match_engine.get_best_score_between_users(user, opted_user)
        # opted_user_score = users_scoring.get_user_score(opted_user)
        user_match_score_map[opted_user.email] = [final_score, detailed_score]

    # Removing user's match with the user itself.
    try:
        user_match_score_map.pop(user.email)
    except KeyError:
        pass

    # Sorting the user match score.
    sorted_user_match_score_map = {k: v for k, v in sorted(
        user_match_score_map.items(), key=lambda item: item[1], reverse=True
    )}

    # Get top 10 users.
    results = dict(islice(sorted_user_match_score_map.items(), 10))

    # Initializing final results with user's info as well.
    final_results = [
        {
            "email": user.email,
            "user_info": get_user_info(user)
        }
    ]
    for email, score_list in results.items():
        matched_user = get_user_model().objects.get(email=email)
        data = {
            "email": email,
            "user_id": matched_user.pk,
            "match_score": score_list[0],
            # These are detailed score details.
            constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE: score_list[1].get(constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE),
            constants.TAG_TO_TAG_ENGINE: score_list[1].get(constants.TAG_TO_TAG_ENGINE),
            constants.OBJECTIVE_TO_OBJECTIVE_ENGINE: score_list[1].get(constants.OBJECTIVE_TO_OBJECTIVE_ENGINE),
            constants.INTRODUCTION_TEXT_ENGINE: score_list[1].get(constants.INTRODUCTION_TEXT_ENGINE),
            constants.SECTOR_MATCH_ENGINE: score_list[1].get(constants.SECTOR_MATCH_ENGINE)
        }
        final_results.append(data)

    return final_results


def get_user_info(user):
    """Returns users data used in the engines for visualisation.

    Note:
        This is purely for display and visualisation purposes.

    """

    user_info = {
        "phone_number": user.get_phone_number(),
        "linkedin": user.profile.linkedin_url,
        "source": user.source,
        "tags": None,
        "objectives": None,
        "interests": None,
        "introduction": None
    }

    if user.has_profile:
        user_tags = ",".join(list(user.profile.tags.all().values_list("name", flat=True)))
        user_info["tags"] = user_tags

        user_introduction = user.profile.get_introduction() if user.has_profile else None
        user_info["introduction"] = user_introduction

    latest_meeting_preference = meeting_service.get_latest_meeting_preference(user)
    if not latest_meeting_preference:
        return

    user_objectives = ",".join(list(latest_meeting_preference.objectives.all().values_list("name", flat=True)))
    user_info["objectives"] = user_objectives

    user_interests = ",".join(list(latest_meeting_preference.interests.all().values_list("name", flat=True)))
    user_info["interests"] = user_interests

    return user_info

