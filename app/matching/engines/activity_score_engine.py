from resources.meetings import choices


def get_activity_score_between_users(user, matched_user):
    """Creates a match score for users based on their tags."""

    user_rsvps = user.meeting_rsvps.all()
    user_activity_score = 0

    for rsvp in user_rsvps:
        if rsvp.status == choices.MEETING_RSVP_STATUS_ATTENDING:
            user_activity_score += 10
        elif rsvp.status in [choices.MEETING_RSVP_STATUS_PENDING, choices.MEETING_RSVP_STATUS_NOT_ATTENDING]:
            user_activity_score -= 20

    matched_user_rsvps = matched_user.meeting_rsvps.all()
    matched_user_activity_score = 0

    for rsvp in matched_user_rsvps:
        if rsvp.status == choices.MEETING_RSVP_STATUS_ATTENDING:
            matched_user_activity_score += 10
        elif rsvp.status in [choices.MEETING_RSVP_STATUS_PENDING, choices.MEETING_RSVP_STATUS_NOT_ATTENDING]:
            matched_user_activity_score -= 20

    # TODO(Nishant): Get score for when the user_activity_score is 0 or less than 0 as well.
    activity_score = 0

    if user_activity_score * matched_user_activity_score < 0:
        activity_score = -30
    elif (user_activity_score < 0 and matched_user_activity_score == 0) and (user_activity_score == 0 and matched_user_activity_score < 0):
        activity_score = -20
    elif user_activity_score * matched_user_activity_score > 0:
        activity_score = 10

    return activity_score
