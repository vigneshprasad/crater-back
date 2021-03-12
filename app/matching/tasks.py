from celery.schedules import crontab
from celery.task import periodic_task

from matching import public
from matching import models
from matching import private
from resources.meetings import services as meeting_service


# @periodic_task(run_every=crontab(hour='18', minute='30'))
def create_daily_best_matches_for_opted_in_users(config=None):
    """Creates best matches for all opted in user.

    Args:
        config(meetings.Config): Config object for which we are calculating scores for user's

    """
    opted_in_users = meeting_service.get_opted_in_users_for_config(config=config)

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


def create_conversations_for_opted_in_users(users=None, config=None):
    # Get latest meeting config if not provided.
    config = config if config else meeting_service.get_latest_active_meeting_config()
    # Get opted in users.
    opted_in_users = users if users else meeting_service.get_opted_in_users_for_config(config=config)

    topic_users_set_map = private.create_match_sets_for_opted_in_user(opted_in_users)

    sorted_topic_users_set_map = {}

    for topic, user_set in topic_users_set_map.items():
        sorted_user_set = private.sort_users_by_user_score(user_set)
        sorted_topic_users_set_map[topic] = sorted_user_set

    for topic, user_set in sorted_topic_users_set_map.items():
        private.create_matches_for_user_set(topic, user_set)
