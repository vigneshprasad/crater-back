from users import models as user_models
from matching.engines import users_scoring
from matching import constants


def run(emails):

    print(
        "Email A", ",",
        "Email B", ",",
        "Score A", ",",
        "Score B", ",",
        "Tag to Experience A", ",",
        "Tag to Company type A", ",",
        "Source Score A", ",",
        "Education level A", ",",
        "Activity A", ",",
        "Tag to Experience B", ",",
        "Tag to Company type B", ",",
        "Source Score B", ",",
        "Education level B", ",",
        "Activity B", ",",
    )

    for email_tuple in emails:

        email1, email2 = email_tuple[0], email_tuple[1]
        user1 = user_models.User.objects.get(email=email1)
        user2 = user_models.User.objects.get(email=email2)

        score1, detailed_score1 = users_scoring.calculate_user_score_with_detailed_score(user1)
        score2, detailed_score2 = users_scoring.calculate_user_score_with_detailed_score(user2)

        print(
            user1.email, ",",
            user2.email, ",",
            score1, ",",
            score2, ",",
            detailed_score1[constants.TAG_TO_EXPERIENCE_ENGINE], ",",
            detailed_score1[constants.TAG_TO_COMPANY_TYPE_ENGINE], ",",
            detailed_score1[constants.SOURCE_ENGINE], ",",
            detailed_score1[constants.EDUCATION_LEVEL_ENGINE], ",",
            detailed_score1[constants.ACTIVITY_ENGINE], ",",
            detailed_score2[constants.TAG_TO_EXPERIENCE_ENGINE], ",",
            detailed_score2[constants.TAG_TO_COMPANY_TYPE_ENGINE], ",",
            detailed_score2[constants.SOURCE_ENGINE], ",",
            detailed_score2[constants.EDUCATION_LEVEL_ENGINE], ",",
            detailed_score2[constants.ACTIVITY_ENGINE], ",",
        )
