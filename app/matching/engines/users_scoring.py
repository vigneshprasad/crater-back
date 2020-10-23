from matching.engines import scoring_constants
from matching import constants


def get_user_score(user):
    """Get user score based on multiple factors."""
    user_score = 0

    tag_based_score = get_user_score_based_on_tags(user)
    user_score += tag_based_score

    source_based_score = get_user_score_based_on_source(user)
    user_score += source_based_score

    return user_score


def get_user_score_based_on_tags(user):
    """Get the user's score based on the user's tags."""
    user_tag_score = 0

    if not user.has_profile:
        return 100

    tags = user.profile.tags.all().values_list("name", flat=True)
    tags_count = len(tags)

    if not tags:
        return 100

    for tag in tags:
        user_tag_score += scoring_constants.BASE_TAG_SCORES_FOR_USER.get(tag, 100)

    #  Returning average tag score for user. To keep similarity between user's with
    # difference number of tags.

    return user_tag_score / tags_count


def get_user_score_based_on_source(user):
    source = user.source
    if not source:
        return 0

    if source == constants.KEZIAH_TYPEFORM:
        return 50

    return 0
