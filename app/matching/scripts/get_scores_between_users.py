from users import models as user_models
from matching import public


def run(emails=None):
    """Takes emails and calculate match scores between those users."""
    if not emails:
        print("No emails provided.")
        return

    print("Total emails: {}".format(len(emails)))

    users = user_models.User.objects.filter(email__in=emails)
    print("Total Users: {}".format(users.count()), "\n")
    for user in users:
        print(user.email, "\n")
        top_matches = public.get_top_matches_for_user(user, match_with=users)
        for top_match in top_matches:
            print(top_match["email"], top_match["match_score"])
        print("-"*30)
