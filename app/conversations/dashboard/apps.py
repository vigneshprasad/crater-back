from django.apps import AppConfig


class ConversationDashboardConfig(AppConfig):

    name = "conversations.dashboard"
    label = "conversations_dashboard"

    def ready(self):
        pass
