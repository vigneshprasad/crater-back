from matching import constants
from matching.engines import scoring_constants
from resources.meetings import services as meeting_services


def get_user_score(user):
    """Get user score based on multiple factors."""
    user_score = 0

    detailed_score = {
        constants.TAG_TO_EXPERIENCE_ENGINE: get_user_score_based_on_tags_and_experience(user),
        constants.TAG_TO_COMPANY_TYPE_ENGINE: get_user_score_based_on_tags_and_company_type(user),
        constants.SOURCE_ENGINE: get_user_score_based_on_source(user),
        constants.EDUCATION_LEVEL_ENGINE: get_user_score_based_on_education(user),
        constants.ACTIVITY_ENGINE: get_user_activity_score(user)
    }
    # Adding a print for visualization.
    print(detailed_score)

    for key, value in constants.USER_SCORE_ENGINE_WEIGHTAGES.items():
        user_score += detailed_score.get(key) * value

    return user_score


def get_user_score_based_on_tags_and_experience(user):
    """Returns score based on user's tag and years of experience."""
    if not user.has_profile:
        return 0

    user_tag_to_experience_score = 0
    tags = user.profile.tags.all().values_list("name", flat=True)
    years_of_experience = user.profile.years_of_experience

    if not (tags and years_of_experience):
        return 0

    for tag in tags:
        tag_score = scoring_constants.TAG_TO_EXPERIENCE_SCORES.get(tag, {})
        user_tag_to_experience_score += tag_score.get(years_of_experience, 0)

    return user_tag_to_experience_score/len(tags)


def get_user_score_based_on_tags_and_company_type(user):
    """Returns score based on tag and user's company type."""
    if not user.has_profile:
        return 0

    user_tag_to_experience_score = 0
    tags = user.profile.tags.all().values_list("name", flat=True)
    company_type = user.profile.company_type

    if not (tags and company_type):
        return 0

    for tag in tags:
        tag_score = scoring_constants.TAG_TO_EXPERIENCE_SCORES.get(tag, {})
        user_tag_to_experience_score += tag_score.get(company_type, 0)

    return user_tag_to_experience_score/len(tags)


def get_user_score_based_on_education(user):
    """Get the user's score based on the user education level."""
    if not user.has_profile:
        return 0

    education = user.profile.education_level

    if not education:
        return 0

    return scoring_constants.EDUCATION_LEVEL_SCORES.get(education, 0)


def get_user_score_based_on_source(user):
    """Returns score based on user's signup source."""
    user_source = user.new_source
    if not user_source:
        return 50

    return user_source.score


def get_user_activity_score(user):
    """Returns score based on number of meeting a user has had.

    Note:
        TODO(Nishant): Include groups into this once groups are live.

    """
    meetings = meeting_services.get_meetings_attended(user)

    if not meetings:
        return 0

    return meetings.count() * 10
