from matching.engines import new_scoring_constants


def get_tag_to_tag_score_for_users(user, matched_user, user_tag, matched_user_tag):
    """Creates a match score for users based on their tags."""

    if not (user.has_profile and matched_user.profile):
        return 0

    if not (user_tag and matched_user_tag):
        return 0

    from_user_to_matched_user_tag_score = new_scoring_constants.TAG_TO_TAG_SCORES.get(user_tag, {}).get(matched_user_tag, 0)
    from_matched_user_to_user_tag_score = new_scoring_constants.TAG_TO_TAG_SCORES.get(matched_user_tag, {}).get(user_tag, 0)

    return (from_matched_user_to_user_tag_score + from_user_to_matched_user_tag_score)/2
