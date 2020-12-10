from celery.schedules import crontab
from celery.task import periodic_task

from matching import public
from matching import models
from resources.meetings import services as meeting_service


@periodic_task(run_every=crontab(hour='18', minute='30'))
def create_daily_best_matches_for_opted_in_users():
    """Creates best matches for all opted in user's daily."""
    opted_in_users = meeting_service.get_opted_in_user_for_meetings()

    for opted_in_user in opted_in_users:
        final_scores = public.get_top_matches_for_user(opted_in_user)

        for final_score in final_scores:
            user_id = final_score.pop('user_id')
            match_score = final_score.pop('match_score')
            final_score.pop('email')
            detailed_score = final_score

            # Creating user matching score for opted in user.
            models.UserToUserMatchScore.objects.update_or_create(
                user=opted_in_user,
                matched_user_id=user_id,
                defaults={
                  'score': match_score,
                  'detailed_score': detailed_score
                }
            )
