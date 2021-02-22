from users import models as user_models
from matching import public


def get_top_matches(emails=None):
    """Takes emails and spits out the best for the user.

    Note:
        The function won't always spit of matches for a user.

    """
    if not emails:
        print("No emails provided.")
        return

    print("Total emails: {}".format(len(emails)))
    matched_users = []
    users = user_models.User.objects.filter(email__in=emails)
    print("Total Users: {}".format(users.count()), "\n")
    for user in users:
        # If user is already matched, don't match again.
        if user.email in matched_users:
            continue

        # Once we start matching add the user email to matched users list.
        matched_users.append(user.email)
        match_with = users.exclude(email__in=matched_users)
        top_matches = public.get_top_matches_for_user(user, match_with=match_with)

        for top_match in top_matches:
            if top_match["email"] in matched_users:
                continue
            print(user.email, ",", top_match["email"], ",", top_match["match_score"])
            # Add the user matched to matched users list.
            matched_users.append(top_match["email"])
            break

        print("-"*30)
