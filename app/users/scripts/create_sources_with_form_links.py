from users import models
from users import choices


def create_base_sources():
    for source_name, score in choices.BASE_SOURCE_TO_SCORE_MAP.items():
        base_source, _ = models.BaseSource.objects.get_or_create(
            name=source_name,
            score=score
        )


def create_initial_sources():
    for link, source in choices.TYPEFORM_URL_TO_SOURCE_MAP.items():
        base_source = models.BaseSource.objects.get(name=source[0])
        source, _ = models.Source.objects.get_or_create(
            name=source[1],
            base_source=base_source,
            link=link,
            score=base_source.score
        )


def map_users_old_source_to_new_sources(users=None):
    all_users = users if users else models.User.objects.all()
    for user in all_users:
        old_source = user.source
        new_source = choices.EXISTING_SOURCES_TO_NEW_SOURCE_MAP.get(old_source, ("Organic", "Organic")) if old_source else ("Organic", "Organic")
        base_source, _ = models.BaseSource.objects.get_or_create(
            name=new_source[0]
        )
        source, _ = models.Source.objects.get_or_create(
            base_source=base_source,
            name=new_source[1]
        )

        try:
            user.new_source = source
            user.save()
        except Exception:
            continue
