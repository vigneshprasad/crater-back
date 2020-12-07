from users import models as users_model
from matching import models
from matching import public


def run(dry_run=True):
    users = users_model.User.objects.all()
    for user in users:
        score = public.get_user_matching_score(user)
        print("{}: {}".format(user.email, score))
        if not dry_run:
            models.MatchScore.objects.get_or_create(
                user=user,
                score=score
            )
