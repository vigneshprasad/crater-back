from django.contrib.auth import get_user_model

from resources.meetings import services as meeting_services
from matching.engines import user_matching
from matching.engines import matching_constants


def create_match_sets_for_opted_in_user(users=None):
    """Calculates user sets based on their topic.

    Returns:
        Map of topics with respective user sets.

    """
    opted_in_users = users if users else meeting_services.get_opted_in_user_for_meetings()
    create_topic_to_match_set_map = {}

    for opted_in_user in opted_in_users:
        meeting_preference = meeting_services.get_latest_meeting_preference(opted_in_user)

        topic_list = []
        topic = topic_list.append(meeting_preference.topic.name)
        objective = meeting_preference.objectives.first()
        topic_list.append(objective.name) if objective else topic_list

        for topic in topic_list:
            if not create_topic_to_match_set_map.get(topic):
                create_topic_to_match_set_map[topic] = []
                create_topic_to_match_set_map[topic].append(opted_in_user)
            else:
                create_topic_to_match_set_map[topic].append(opted_in_user)

    return create_topic_to_match_set_map


def sort_users_by_user_score(user_set):
    """Sorts a user set by their respective user scores.

    Args:
        user_set(List/Queryset): User's list to be sorted by score.

    Returns:
        Sorted list of users by their respective scores.

    """
    user_to_user_score_map = {}

    for user in user_set:
        # TODO(Nishant): Calculate scores for all users.
        user_to_user_score_map[user.email] = user.score

    sorted_user_set = [k for k, v in sorted(
        user_to_user_score_map.items(), key=lambda item: item[1], reverse=True
    )]
    return sorted_user_set


def create_matches_for_user_set(topic, user_set):
    """Creates matches between the user set provided and score them based on
        topic.

    Args:
        topic(str): Topic we are matching the user set for.
        user_set(list): List of users to be matched among themselves.

    """
    # TODO(Nishant): Handle same users being in multiple user sets.
    matched_users = []

    for user in user_set:
        if user in matched_users:
            continue

        matched_users.append(user)
        final_match_score = 0
        match_score = 0
        match_list = [user]
        final_match_list = []

        while final_match_score >= match_score:

            # Get the last matched user as the user to be matched.
            user_to_be_matched = match_list[len(match_list) - 1]
            final_match_list.append(user_to_be_matched)
            match_score = final_match_score

            # Pop the user from user set.
            user_set.pop(user_to_be_matched)
            matched_user_data = user_matching.get_top_match_for_user(user_to_be_matched, user_set)
            matched_user = get_user_model().objects.get(matched_user_data["email"])
            # Append the user to match list to calculate user score.
            match_list.append(matched_user)

            # Calculate the final match score
            final_match_score += matched_user_data["match_score"]
            final_match_score = final_match_score/len(match_list)
            if len(match_list) > 2:
                final_match_score = final_match_score * matching_constants.TOPIC_GROUP_MULTIPLIER.get(topic, 1.2)

        print(final_match_list, "----", final_match_score)
