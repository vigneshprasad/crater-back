from matching.engines import new_scoring_constants


def get_sector_to_sector_score_for_users(user, matched_user, user_sector, matched_user_sector):
    """Creates a match score for users based on their tags."""

    if not (user.has_profile and matched_user.profile):
        return 0

    if not (user_sector and matched_user_sector):
        return 0

    from_user_to_matched_user_sector_score = new_scoring_constants.SECTOR_TO_SECTOR_SCORES.get(user_sector, {}).get(matched_user_sector, 0)
    from_matched_user_to_user_sector_score = new_scoring_constants.SECTOR_TO_SECTOR_SCORES.get(matched_user_sector, {}).get(user_sector, 0)

    return (from_matched_user_to_user_sector_score + from_user_to_matched_user_sector_score)/2
