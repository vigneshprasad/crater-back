"""Engine creates a match score between two users.

This engine create a score for users matching with each other
and takes both users preferences into consideration before
creating a match.

"""

import nltk
import numpy
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

from matching import constants
from matching.engines import scoring_constants
from resources.meetings import services as meeting_services


def get_match_score_between_users(user1, user2):
    """Get a matching score between two users.

    Note:
        This calculates the score for these user's
            matching/meeting each other. So the score
            will be constant for user1 matching with
            user2 and vice versa.

    """

    detailed_score = {
        constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE: 0,
        constants.TAG_TO_TAG_ENGINE: 0,
        constants.OBJECTIVE_TO_OBJECTIVE_ENGINE: 0,
        constants.INTRODUCTION_TEXT_ENGINE: 0,
        constants.SECTOR_MATCH_ENGINE: 0
    }

    engine_1_score = get_interest_objective_to_tag_score_for_users(user1, user2)
    detailed_score[constants.INTEREST_TO_OBJECTIVE_TAG_ENGINE] = round(engine_1_score, 2)

    engine_2_score = get_tag_to_tag_score_for_users(user1, user2)
    detailed_score[constants.TAG_TO_TAG_ENGINE] = round(engine_2_score, 2)

    engine_3_score = get_objective_to_objective_score_for_users(user1, user2)
    detailed_score[constants.OBJECTIVE_TO_OBJECTIVE_ENGINE] = round(engine_3_score, 2)

    engine_4_score = get_intro_score_for_users(user1, user2)
    detailed_score[constants.INTRODUCTION_TEXT_ENGINE] = round(engine_4_score, 2)

    engine_5_score = get_sector_score_for_users(user1, user2)
    detailed_score[constants.SECTOR_MATCH_ENGINE] = round(engine_5_score, 2)

    match_score = round((engine_1_score + engine_2_score + engine_3_score + engine_4_score + engine_5_score) / 5, 2)

    # Print for testing and visualisation.
    print("User {} matched with {} has a score of: {}".format(user1.email, user2.email, match_score))

    return match_score, detailed_score


def get_objective_to_objective_score_for_users(user1, user2):
    """Creates a match score between two user's based on their meeting objectives."""
    users = [user1, user2]

    score_for_users = 0
    for user in users:
        # Get latest meeting preferences filled by the user, if not return.
        latest_meeting_preference = meeting_services.get_latest_meeting_preference(user)
        if not latest_meeting_preference:
            return 0

        objectives = latest_meeting_preference.objectives.all().values_list("name", flat=True)
        objectives_count = objectives.count()

        to_user = user2 if user == user1 else user1

        # Get meeting preference for the other user and objectives from that.
        to_meeting_preference = meeting_services.get_latest_meeting_preference(to_user)
        if not to_meeting_preference:
            return 0

        to_objectives = to_meeting_preference.objectives.all().values_list("name", flat=True)
        to_objectives_count = to_objectives.count()

        if not (objectives_count and to_objectives_count):
            return 0

        score_for_objectives = 0
        # Get score for all objectives against each other.

        for objective in objectives:
            score_for_to_objectives = 0

            for to_objective in to_objectives:
                # Handling the case where some objectives won't have the scoring dicts. So
                # mapping the old objectives to new ones and then getting score.
                get_score_map_for_objective = scoring_constants.OBJECTIVE_TO_OBJECTIVE_SCORES.get(objective)

                if not get_score_map_for_objective:
                    objective = constants.OLD_OBJECTIVES_TO_NEW_OBJECTIVES_MAP.get(objective)
                    get_score_map_for_objective = scoring_constants.OBJECTIVE_TO_OBJECTIVE_SCORES.get(objective)

                score_for_to_objectives += get_score_map_for_objective.get(to_objective, 0.1)\
                    if get_score_map_for_objective else 0.1

            # Averaging out based on the number of objectives the score was accounted for.
            score_for_objectives = score_for_to_objectives/to_objectives_count

        score_for_users += (score_for_objectives/objectives_count)

    return score_for_users / len(users) * constants.DEFAULT_OBJECTIVE_MULTIPLIER


def get_tag_to_tag_score_for_users(user1, user2):
    """Creates a match score for users based on their tags."""
    users = [user1, user2]
    users_tag_score = 0

    for user in users:
        if not user.has_profile:
            return 0

        tags = user.profile.tags.all().values_list("name", flat=True)
        tags_count = tags.count()
        # Getting the other user's tag for scoring.
        to_user = user2 if user == user1 else user1
        if not to_user.has_profile:
            return 0

        to_tags = to_user.profile.tags.all().values_list("name", flat=True)
        to_tags_count = to_tags.count()

        if not (tags_count and to_tags_count):
            return 0

        score_for_tag = 0

        for tag in tags:
            # If score map for tags is not present, give default 0.1 score for the tag.
            score_map_for_tag = scoring_constants.TAG_TO_TAG_SCORES.get(tag)
            if not score_map_for_tag:
                tags_count -= 1
                continue

            score_for_to_tag = 0

            for to_tag in to_tags:
                score_for_to_tag += score_map_for_tag.get(to_tag, 0.1)
            # Getting average for each tag score based of how many to_tags are present for each tag.
            score_for_tag += (score_for_to_tag/to_tags_count)
        if not tags_count:
            return 0
        # Averaging the score based on the number of user's tags we have calculated the score for.
        users_tag_score += (score_for_tag/tags_count)

    # Returning average score, diving by 2 for 2 users.
    return users_tag_score / len(users)


def get_interest_objective_to_tag_score_for_users(user1, user2):
    """Creates a match score for users based on interest-objective to tag match up for users.

    Note:
        Creating both average and max scores for this engine, only returns the max score for now.

    """
    users = [user1, user2]

    score_for_users = 0
    max_score_for_users = 0

    for user in users:
        latest_meeting_preference = meeting_services.get_latest_meeting_preference(user)
        if not latest_meeting_preference:
            return 0

        interests = latest_meeting_preference.interests.all()
        objectives = latest_meeting_preference.objectives.all()
        # If the user doesn't have interest or objectives, return 0.
        if not (interests and objectives):
            return 0

        interest_objective_map = []
        # Create interest-objective map for scoring.
        for interest in interests:
            for objective in objectives:
                # Handling old interest and objective mapping to new ones.
                new_objective = constants.OLD_OBJECTIVES_TO_NEW_OBJECTIVES_MAP.get(objective.name) or objective.name
                new_interest = constants.OLD_INTERESTS_TO_NEW_INTERESTS_MAP.get(interest.name) or interest.name
                interest_objective_map.append("{} - {}".format(new_interest, new_objective))

        to_user = user2 if user == user1 else user1
        to_user_tags = to_user.profile.tags.all().values_list("name", flat=True)
        to_user_tags_count = to_user_tags.count()

        # If the user doesn't have tags, return 0.
        if not to_user_tags_count:
            return 0

        aggregate_score = 0
        max_score = 0

        # For each interest-objective key pull out score with respect to the other user.
        for interest_objective in interest_objective_map:
            max_score_per_interest_objective = 0
            tags_score_dict = scoring_constants.INTEREST_OBJECTIVE_TAG_SCORE.get(interest_objective)
            if not tags_score_dict:
                aggregate_score += 0.1
                max_score_per_interest_objective = max(max_score_per_interest_objective, 0.1)
                max_score += max_score_per_interest_objective
                continue

            # Add score from all tags that are present.
            tags_score = 0
            for tag in to_user_tags:
                score = float(tags_score_dict.get(tag, 0.1))
                tags_score += score
                max_score_per_interest_objective = max(
                    max_score_per_interest_objective,
                    score
                )

            aggregate_score += (tags_score/to_user_tags_count)
            max_score = max(max_score, max_score_per_interest_objective)

        average_score = aggregate_score/len(interest_objective_map)
        max_score_for_users = max(max_score, max_score_for_users)
        score_for_users += average_score

    return max_score_for_users / len(users)


def get_intro_score_for_users(user1, user2):
    """Creates a score between users based on users intros."""
    users = [user1, user2]
    intro_list = []
    lemmantizer = WordNetLemmatizer()

    if not (user1.has_profile and user2.has_profile):
        return 0

    if not (user1.profile.get_introduction() and user2.profile.get_introduction()):
        return 0

    user_intro_len = len(nltk.word_tokenize(user1.profile.get_introduction()))
    user2_intro_len = len(nltk.word_tokenize(user2.profile.get_introduction()))

    for user in users:
        words = nltk.word_tokenize(user.profile.get_introduction())
        if len(words) < constants.INTRO_MIN_LENGTH:
            return 0
        words = [lemmantizer.lemmatize(word, pos='v') for word in words]
        intro_list.append(' '.join(words).lower())

    vector = TfidfVectorizer(min_df=1, stop_words='english')
    try:
        vector_transform = vector.fit_transform(intro_list)
    except ValueError:
        # This is to handle if intro's are not meaningful and contain only stop words.
        return 0

    pairwise_similarity = vector_transform * vector_transform.T
    array = pairwise_similarity.toarray()
    numpy.fill_diagonal(array, 0)

    # Handling small intros 
    if user_intro_len > constants.INTRO_REDUCTION_LENGTH:
        intro_len_factor = 1
    else:
        # The number 10 has been chosen arbitrarily here and can be
        # potentially tweaked. Current idea is that it is a sigmoid 
        # function with a mean chosen as half of 20. 
        intro_len_factor = 1 / (1 + numpy.exp(-(user_intro_len / (constants.INTRO_REDUCTION_LENGTH / 2))))

    # Averaging the score for user intros.
    average_score_for_user_intros = (array[0][1]) * intro_len_factor

    return average_score_for_user_intros * constants.DEFAULT_INTRO_MULTIPLIER


def get_sector_score_for_users(user1, user2):
    """Creates a score between users based on users intros."""

    # TODO(Nishant): Create these from KEYWORDS_SECTOR.values() or store as constants.
    user1_sector = {
        "Accounts": 0,
        "Agriculture": 0,
        "AI": 0,
        "Bio": 0,
        "Chemical": 0,
        "Computer": 0,
        "Consulting": 0,
        "Data": 0,
        "Design": 0,
        "ECommerce": 0,
        "Education": 0,
        "Electrical": 0,
        "Energy": 0,
        "Environment": 0,
        "Event": 0,
        "Fashion": 0,
        "Film": 0,
        "Financial": 0,
        "Food": 0,
        "Gaming": 0,
        "Healthcare": 0,
        "HR": 0,
        "Investor": 0,
        "Law": 0,
        "Marketing": 0,
        "Mechanical": 0,
        "Media": 0,
        "Mental Health": 0,
        "Photography": 0,
        "Politics": 0,
        "Product": 0,
        "Real Estate": 0,
        "Social": 0,
        "Startup": 0,
        "Travel": 0,
    }
    user2_sector = {
        "Accounts": 0,
        "Agriculture": 0,
        "AI": 0,
        "Bio": 0,
        "Chemical": 0,
        "Computer": 0,
        "Consulting": 0,
        "Data": 0,
        "Design": 0,
        "ECommerce": 0,
        "Education": 0,
        "Electrical": 0,
        "Energy": 0,
        "Environment": 0,
        "Event": 0,
        "Fashion": 0,
        "Film": 0,
        "Financial": 0,
        "Food": 0,
        "Gaming": 0,
        "Healthcare": 0,
        "HR": 0,
        "Investor": 0,
        "Law": 0,
        "Marketing": 0,
        "Mechanical": 0,
        "Media": 0,
        "Mental Health": 0,
        "Photography": 0,
        "Politics": 0,
        "Product": 0,
        "Real Estate": 0,
        "Social": 0,
        "Startup": 0,
        "Travel": 0,
    }

    lemmantizer = WordNetLemmatizer()

    if not (user1.has_profile and user2.has_profile):
        return 0

    if not (user1.profile.get_introduction() and user2.profile.get_introduction()):
        return 0

    words = nltk.word_tokenize(user1.profile.get_introduction())
    words = [lemmantizer.lemmatize(word, pos='v') for word in words]

    for word in words:
        if word not in scoring_constants.KEYWORDS_SECTOR.keys():
            continue

        sector = scoring_constants.KEYWORDS_SECTOR[word]
        user1_sector[sector] = user1_sector[sector] + 1

    words = nltk.word_tokenize(user2.profile.get_introduction())
    words = [lemmantizer.lemmatize(word, pos='v') for word in words]

    for word in words:
        if word not in scoring_constants.KEYWORDS_SECTOR.keys():
            continue

        sector = scoring_constants.KEYWORDS_SECTOR[word]
        user2_sector[sector] = user2_sector[sector] + 1

    v1 = list(user1_sector.values())
    v2 = list(user2_sector.values())

    cosine = numpy.dot(v1, v2) / (numpy.sqrt(numpy.dot(v1, v1)) * numpy.sqrt(numpy.dot(v2, v2)))

    if numpy.isnan(cosine):
        return 0

    return cosine * constants.DEFAULT_SECTOR_MULTIPLIER
