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
    matched_users = []
    for user in users:
        # If user has already been matched, don't match again.
        if user.email in matched_users:
            continue
        matched_users.append(user.email)

        top_matches = public.get_top_matches_for_user(user, match_with=users)
        for top_match in top_matches:
            if top_match["email"] in matched_users:
                continue
            print(user.email, ",", top_match["email"])
            matched_users.append(top_match["email"])
            break

        print("-"*30)
