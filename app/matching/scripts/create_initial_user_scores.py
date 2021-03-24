from users import models as users_model
from matching import models
from matching import public


def run(users=None, dry_run=True):
    """Create Initial Score for all users."""
    users = users if users else users_model.User.objects.all()

    for user in users:
        score = public.calculate_user_score(user)
        print("{}: {}".format(user.email, score))

        if not dry_run:
            user_score = models.UserScore.objects.filter(
                user=user
            ).last()

            if not user_score:
                user_score = models.UserScore.objects.create(
                    user=user,
                    score=score
                )

            user_score.score = score
            user_score.save()
            # Adding to user score field as well.
            try:
                user.score = score
                user.save()
            except TypeError:
                print(user.email)
