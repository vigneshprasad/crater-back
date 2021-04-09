from django.db.models import Q

from conversations import models
from conversations import constants
from resources.meetings import models as meeting_models


def run(dry_run=True):

    preferences_without_topic = meeting_models.MeetingPreference.objects.filter(
        Q(topic__isnull=True) | Q(topic__name="Default")
    )

    for preference in preferences_without_topic:
        # Preference object already has a topic.
        if preference.topic:
            continue

        print("Preference: ", preference.id)

        objectives = preference.objectives.all()
        print("Objectives: ", objectives)

        topic_names = []

        for objective in objectives:
            topic_name = constants.OBJECTIVE_TO_TOPIC_MAP.get(objective.name)
            if not topic_name:
                continue
            topic_names.append(topic_name)

        if not topic_names:
            print("No Match Found.")

        topic = models.Topic.objects.filter(name__in=topic_names).first()

        if not topic:
            # Doing a filter in case Default topic is not present on the environment.
            topic = models.Topic.objects.filter(name=constants.DEFAULT_TOPIC_NAME).first()

        print("Topic: ", topic)

        if not dry_run:

            print("Updating Topic for Preference: ", preference.id)
            preference.topic = topic
            preference.save()
