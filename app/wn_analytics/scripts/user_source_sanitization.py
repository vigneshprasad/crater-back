from django.contrib.auth import get_user_model

from wn_analytics import models

anand_user = get_user_model().objects.get(pk='e6a66828-9a79-45d2-9889-43fc623663b9')
sundeep_user = get_user_model().objects.get(pk='2323e66a-e0b8-4378-ad90-712859c624b4')

SOURCE_TO_NEW_SOURCE = {
    "facebook": {
        "utm_source": "Facebook",
        "referrer": None
    },
    "Facebook+StaticPost+Website": {
        "utm_source": "Facebook",
        "referrer": None
    },
    "Fb": {
        "utm_source": "Facebook",
        "referrer": None
    },
    "fb": {
        "utm_source": "Facebook",
        "referrer": None
    },
    "linkedin": {
        "utm_source": "LinkedIn",
        "referrer": None
    },
    "Anand K Rathi": {
        "utm_source": "Wealth School",
        "referrer": anand_user
    },
    "Slack": {
        "utm_source": "Slack",
        "referrer": sundeep_user
    },
    "Discord":  {
        "utm_source": "Discord",
        "referrer": sundeep_user
    }
}


def delete_sources(dry_run=True):

    user_sources = models.UserSource.objects.all()
    to_delete = []

    for user_source in user_sources:

        print("------")

        utm_source = user_source.utm_source
        utm_medium = user_source.utm_medium
        utm_campaign = user_source.utm_campaign

        user = user_source.user
        is_crater = user.groups.filter(name="crater_club").exists()

        print("UTM Source ", utm_source)
        print("Is Crater", is_crater)

        if not is_crater:
            # If the user was in worknetwork, delete.
            to_delete.append(user_source.id)

        if not (utm_source and utm_medium and utm_campaign):
            # If the user has no source, medium and campaign, delete.
            if user_source.id not in to_delete:
                user = user_source.user
                print("To be deleted: {}".format(user_source.id))
                to_delete.append(user_source.id)

        if utm_source == "null":
            # If the utm source is null, delete.
            if user_source.id not in to_delete:
                user = user_source.user
                is_crater = user.groups.filter(name="crater_club").exists()
                if is_crater:
                    print("To be deleted: {}".format(user_source.id))
                    to_delete.append(user_source.id)

        print("------")

    if to_delete:
        print("Deleting {} user sources".format(len(to_delete)))
        if not dry_run:
            to_delete_queryset = models.UserSource.objects.filter(id__in=to_delete)
            c = to_delete_queryset.delete(soft=False)
            print("Deleted {} user sources".format(c))


def update_sources(dry_run=True):

    user_sources = models.UserSource.objects.all()
    for user_source in user_sources:

        utm_source = user_source.utm_source
        utm_medium = user_source.utm_medium
        utm_campaign = user_source.utm_campaign

        if utm_source in SOURCE_TO_NEW_SOURCE.keys():
            print("Original Data")
            print(user_source.id)
            print(utm_source, "|", utm_medium, "|", utm_campaign)

            new_source_data = SOURCE_TO_NEW_SOURCE[utm_source]

            print("Updating the utm source and referrer to: {} - {}".format(
                new_source_data["utm_source"],
                new_source_data["referrer"])
            )

            if not dry_run:
                user_source.utm_source = new_source_data["utm_source"]
                user_source.referrer = new_source_data["referrer"]
                user_source.save()
                print("Updated")
