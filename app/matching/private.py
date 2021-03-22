import itertools

from django.contrib.auth import get_user_model

from resources.meetings import services as meeting_services
from matching.engines import user_matching
from matching.engines import users_scoring
from matching.engines import matching_constants


def create_matches_for_all_opted_in_users(users=None):
    """Creates matches for all opted in users or users if provided."""
    topic_match_sets_maps = create_match_sets_for_opted_in_user(users=users)

    for topic, user_set in topic_match_sets_maps.items():
        # Creates matches for a given topic and user set.
        create_matches_for_user_set(topic, user_set)


def create_match_sets_for_opted_in_user(users=None):
    """Calculates user sets based on their topic.

    Returns:
        Map of topics with respective user sets.

    """
    opted_in_users = users if users else meeting_services.get_opted_in_user_for_meetings()
    topic_to_match_set_map = {}

    for opted_in_user in opted_in_users:

        meeting_preference = meeting_services.get_latest_meeting_preference(opted_in_user)
        # If the user doesn't have meeting preference move to the next user.
        if not meeting_preference:
            continue

        initial_topic = meeting_preference.topic
        initial_objective = meeting_preference.objectives.first()
        if not (initial_objective or initial_topic):
            continue

        topic = initial_topic.name if initial_topic else initial_objective.name

        if not topic_to_match_set_map.get(topic):
            topic_to_match_set_map[topic] = []
            topic_to_match_set_map[topic].append(opted_in_user)
        else:
            topic_to_match_set_map[topic].append(opted_in_user)

    sorted_topic_to_match_set_map = {}
    # Sort the user sets for each topic.
    for topic, user_set in topic_to_match_set_map.items():
        sorted_topic_to_match_set_map[topic] = sort_users_by_user_score(user_set)

    return sorted_topic_to_match_set_map


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
        user_to_user_score_map[user] = user.score

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
    all_matches = []

    for user in user_set:
        if user in matched_users:
            continue

        matched_users.append(user)
        final_match_score = 0
        match_score = 0
        match_list = [user]
        final_match_list = []

        while final_match_score >= match_score and len(final_match_list) <= matching_constants.DEFAULT_GROUP_SIZE:

            # Get the last matched user as the user to be matched.
            user_to_be_matched = match_list[len(match_list) - 1]
            final_match_list.append(user_to_be_matched)
            match_score = final_match_score

            # Pop the user from user set.
            matched_user_data = user_matching.get_top_match_for_user(user_to_be_matched, user_set)
            # If the user has no good match. Break and start with the next user.
            if not matched_user_data:
                break

            matched_user = get_user_model().objects.get(email=matched_user_data["email"])
            # Append the user to match list to calculate user score.
            match_list.append(matched_user)

            # Calculate the final match score
            final_match_score = get_group_match_score(match_list)
            if len(match_list) > 2:
                final_match_score = final_match_score * matching_constants.TOPIC_GROUP_MULTIPLIER.get(topic, 1.2)

        # Append the final match list to matched users.
        for final_matched_user in final_match_list:
            matched_users.append(final_matched_user)

        final_match_list_with_score = []
        for final_matched_user in final_match_list:
            final_match_list_with_score.append((final_matched_user.email, users_scoring.get_user_score(final_matched_user)))

        print(final_match_list_with_score, "-", get_average_group_score_based_on_user_score(final_match_list), "-", final_match_score)

        all_matches.append((final_match_list_with_score, final_match_score))

    return all_matches


def get_group_match_score(users):
    """Calculates group score between all users provided."""
    all_user_sets = list(itertools.permutations(users, 2))
    group_score = 0

    for user, matched_user in all_user_sets:
        match_score, _ = user_matching.get_match_score_between_users(user, matched_user)
        group_score += match_score

    return group_score/len(all_user_sets)


def get_average_group_score_based_on_user_score(users):
    """Calculate average group score based on user scores."""
    total_score = 0

    for user in users:
        total_score += users_scoring.get_user_score(user)

    return total_score/len(users)
