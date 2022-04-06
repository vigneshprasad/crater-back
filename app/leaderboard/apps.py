from django.apps import AppConfig


class LeaderboardConfig(AppConfig):
    name = "leaderboard"

    def ready(self):
        import leaderboard.receivers
