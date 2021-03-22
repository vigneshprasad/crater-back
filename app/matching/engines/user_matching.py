from itertools import islice

from django.contrib.auth import get_user_model

from matching.engines import matching_constants
from matching.engines import tag_to_tag_engine
from matching.engines import tag_to_interest_engine
from matching.engines import sector_to_sector_engine
from matching.engines import activity_score_engine
from matching.engines import user_to_user_score_deviation_engine
from matching.engines import users_scoring
from resources.meetings import services as meeting_services


# Get top 10 matches for user.
def get_top_10_matches_for_user(user, match_set):
    """Calculates top 10 matches for a user.

    Args:
        user(User): User that is to be matched.
        match_set(list): List of user the user is to be matched against.

    Returns:
        List of top 10 matches with their match scores and detailed scores.

    """
    user_match_score_map = {}

    for opted_user in match_set:
        if not opted_user.has_profile:
            continue

        final_score, detailed_score = get_match_score_between_users(user, opted_user)
        user_match_score_map[opted_user.email] = [final_score, detailed_score]

    # Removing user's match with the user itself.
    try:
        user_match_score_map.pop(user.email)
    except KeyError:
        pass

    # Sorting the user match score.
    try:
        sorted_user_match_score_map = {k: v for k, v in sorted(
            user_match_score_map.items(), key=lambda item: item[1][0], reverse=True
        )}
    except TypeError:
        sorted_user_match_score_map = user_match_score_map

    # Return top 10 users.
    results = dict(islice(sorted_user_match_score_map.items(), 10))
    final_results = []

    for email, score_list in results.items():
        try:
            matched_user = get_user_model().objects.get(email=email)
        except (get_user_model().MultipleObjectsReturned, get_user_model().DoesNotExist):
            continue

        data = {
            "email": email,
            "user_id": matched_user.pk,
            "match_score": score_list[0],
            # These are detailed score details.
            matching_constants.TAG_TO_TAG_ENGINE: score_list[1].get(matching_constants.TAG_TO_TAG_ENGINE),
            matching_constants.TAG_TO_INTEREST_ENGINE: score_list[1].get(matching_constants.TAG_TO_INTEREST_ENGINE),
            matching_constants.SECTOR_TO_SECTOR_ENGINE: score_list[1].get(matching_constants.SECTOR_TO_SECTOR_ENGINE)
        }
        final_results.append(data)

    return final_results


# Get top match for user.
def get_top_match_for_user(user, match_set):
    """Calculates top match for a user.

    Args:
        user(User): User that is to be matched.
        match_set(list): List of user the user is to be matched against.

    Returns:
        Top match for the user with match scores and detailed scores.

    """

    # Removing the user being matched from match set.
    max_match_score = 0
    best_match_user = None
    final_detailed_score = {}

    for matched_user in match_set:

        if not matched_user.has_profile:
            continue

        final_score, detailed_score = get_match_score_between_users(user, matched_user)
        # Getting the best match based on the maximum match score.
        if final_score > max_match_score:
            max_match_score, best_match_user, final_detailed_score = final_score, matched_user, detailed_score

    if not best_match_user:
        return None

    data = {
        "email": best_match_user.email,
        "user_id": best_match_user.pk,
        "match_score": max_match_score,
        # These are detailed score details.
        matching_constants.TAG_TO_TAG_ENGINE: final_detailed_score.get(matching_constants.TAG_TO_TAG_ENGINE),
        matching_constants.TAG_TO_INTEREST_ENGINE: final_detailed_score.get(matching_constants.TAG_TO_INTEREST_ENGINE),
        matching_constants.SECTOR_TO_SECTOR_ENGINE: final_detailed_score.get(matching_constants.SECTOR_TO_SECTOR_ENGINE)
    }

    return data


# Get match score between users.
def get_match_score_between_users(user, matched_user):
    """Calculates match scores between given users.

    Returns:
        Match score and detailed score for the users.

    """
    detailed_score = {
        matching_constants.TAG_TO_TAG_ENGINE: 0,
        matching_constants.TAG_TO_INTEREST_ENGINE: 0,
        matching_constants.SECTOR_TO_SECTOR_ENGINE: 0,
        matching_constants.ACTIVITY_SCORE_ENGINE: 0,
        matching_constants.USER_TO_USER_SCORE_DEVIATION_ENGINE: 0
    }

    if not (user.profile and matched_user.profile):
        return 0

    # Get all user details for optimized DB calls.
    user_profile = user.profile
    matched_user_profile = matched_user.profile

    user_tag = user_profile.new_tag.first()
    matched_user_tag = matched_user_profile.new_tag.first()

    print("User Tag: {}".format(user_tag))
    print("Matched User Tag: {}".format(matched_user_tag))

    latest_user_preference = meeting_services.get_latest_preference_for_user(user)
    latest_matched_user_preference = meeting_services.get_latest_preference_for_user(matched_user)

    user_interests = None
    matched_user_interests = None

    if latest_user_preference:
        user_interests = latest_user_preference.interests.all()

    if latest_matched_user_preference:
        matched_user_interests = latest_matched_user_preference.interests.all()

    print("User Interests: {}".format(user_interests))
    print("Matched User Interests: {}".format(matched_user_interests))

    # TODO(Nishant): See how we can calculate score deviation here.
    user_score = users_scoring.get_user_score(user)
    matched_user_score = users_scoring.get_user_score(matched_user)

    print("User Score: {}".format(user_score))
    print("Matched User Score: {}".format(matched_user_score))

    user_sector = user_profile.sector
    matched_user_sector = matched_user_profile.sector

    print("User Sector: {}".format(user_sector))
    print("Matched User Sector: {}".format(matched_user_sector))

    score_deviation_score = user_to_user_score_deviation_engine.get_score_deviation_score_between_users(
        user_score,
        matched_user_score
    )
    detailed_score[matching_constants.USER_TO_USER_SCORE_DEVIATION_ENGINE] = round(score_deviation_score, 2)

    # Engines score calculation.
    tag_to_tag_engine_score = tag_to_tag_engine.get_tag_to_tag_score_for_users(
        user,
        matched_user,
        user_tag,
        matched_user_tag
    )
    detailed_score[matching_constants.TAG_TO_TAG_ENGINE] = round(tag_to_tag_engine_score, 2)

    tag_to_interest_engine_score = tag_to_interest_engine.get_tag_to_interest_score_for_users(
        user,
        matched_user,
        user_tag,
        matched_user_tag,
        user_interests,
        matched_user_interests
    )
    detailed_score[matching_constants.TAG_TO_INTEREST_ENGINE] = round(tag_to_interest_engine_score, 2)

    sector_to_sector_engine_score = sector_to_sector_engine.get_sector_to_sector_score_for_users(
        user,
        matched_user,
        user_sector,
        matched_user_sector
    )
    detailed_score[matching_constants.TAG_TO_INTEREST_ENGINE] = round(sector_to_sector_engine_score, 2)

    activity_score_engine_score = activity_score_engine.get_activity_score_between_users(
        user,
        matched_user
    )
    detailed_score[matching_constants.ACTIVITY_SCORE_ENGINE] = round(activity_score_engine_score, 2)

    # Calculate final match score for users.
    match_score = get_match_score_from_detailed_score(detailed_score)

    return match_score, detailed_score


def get_match_score_from_detailed_score(detailed_score):
    """Get user match score from the detailed score for users."""

    score = 0

    for key, weightage in matching_constants.ENGINE_WEIGHTAGE_MAP.items():
        score += detailed_score.get(key, 0) * weightage

    return score
