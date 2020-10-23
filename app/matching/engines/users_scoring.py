from matching.engines import scoring_constants


def get_user_score(user):
    """Get user score based on multiple factors."""
    user_score = 0

    tag_based_score = get_user_score_based_on_tags(user)
    user_score += tag_based_score

    return user_score / 1


def get_user_score_based_on_tags(user):
    """Get the user's score based on the user's tags."""
    user_tag_score = 0

    if not user.has_profile:
        return user_tag_score

    tags = user.profile.tags.all().values_list("name", flat=True)
    tags_count = len(tags)

    if not tags:
        return user_tag_score

    for tag in tags:
        user_tag_score += scoring_constants.BASE_TAG_SCORES_FOR_USER.get(tag, 100)

    return user_tag_score / tags_count
