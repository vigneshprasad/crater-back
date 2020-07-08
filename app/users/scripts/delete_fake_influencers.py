from django.contrib.auth import get_user_model
from points.models import UserPoints, PointsLog
from wn_analytics.models import TrackLog, IdentifyLog

User = get_user_model()


def run(user_email_list, dry_run=True):
    users = User.objects.filter(email__in=user_email_list)

    print('User DELETE COUNT:', users.count())

    # Hard Delete User Points, Points Log, Analytics Track and Identify logs
    for user in users:
        user_points = UserPoints.objects.filter(user=user)
        user_logs = PointsLog.objects.filter(user=user)
        user_track_log = TrackLog.objects.filter(user=user)
        user_identify_log = IdentifyLog.objects.filter(user=user)
        print('----------------------USER OBJECT-------------------------------')
        print('email:', user.email)
        print('name:', user.name)

        if user_points:
            print('points:', user_points[0].points)
            if not dry_run:
                user_points.delete(soft=False)

        if user_logs:
            print('points-logs:', user_logs)
            if not dry_run:
                user_logs.delete(soft=False)

        if user_track_log:
            print('track-logs', user_track_log)
            if not dry_run:
                user_track_log.delete(soft=False)

        if user_identify_log:
            print('identify-logs', user_identify_log)
            if not dry_run:
                user_identify_log.delete(soft=False)

        print('-----------------------------------------------------------------\n\n')

    # Hard Delete users
    if not dry_run:
        users.delete()

