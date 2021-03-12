from matching.engines import new_scoring_constants


def get_tag_to_interest_score_for_users(user, matched_user, user_tag, matched_user_tag, user_interests, matched_user_interests):
    """Creates a match score for users based on their tags."""

    if not (user.has_profile and matched_user.profile):
        return 0

    if not (user_tag and matched_user_tag):
        return 0

    if not (user_interests and matched_user_interests):
        return 0

    from_user_to_matched_user_tag_to_interest_score = 0
    for matched_user_interest in matched_user_interests:
        from_user_to_matched_user_tag_to_interest_score += new_scoring_constants.TAG_TO_INTEREST_SCORES.get(user_tag, {}).get(matched_user_interest, 0)

    from_matched_user_to_user_tag_to_interest_score = 0
    for user_interest in user_interests:
        from_matched_user_to_user_tag_to_interest_score += new_scoring_constants.TAG_TO_INTEREST_SCORES.get(matched_user_tag, {}).get(user_interest, 0)

    return (from_matched_user_to_user_tag_to_interest_score/len(user_interests) + from_user_to_matched_user_tag_to_interest_score/len(matched_user_interests))/2
