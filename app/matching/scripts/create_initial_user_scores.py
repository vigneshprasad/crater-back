from users import models as users_model
from matching import models
from matching import public


def run(users=None, dry_run=True):
    """Create Initial Score for all users."""
    users = users if users else users_model.User.objects.all()

    for user in users:
        score = public.get_user_matching_score(user)
        print("{}: {}".format(user.email, score))

        if not dry_run:
            models.UserScore.objects.update_or_create(
                user=user,
                defaults={"score": score}
            )
            # Adding to user score field as well.
            user.score = score
            user.save()
