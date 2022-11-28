from wn_analytics import models, constants


def create_user_source(
        user,
        utm_source=None,
        utm_medium=None,
        utm_campaign=None,
        referrer=None
):
    # One of the three should be present to create user source.
    if not (utm_source or utm_campaign or referrer):
        return

    # Create user source.
    user_source = models.UserSource.objects.create(
        user=user,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        utm_medium=utm_medium,
        referrer=referrer
    )

    # If utm_source is IGC opt out of whatsapp.
    if utm_source == constants.IGC_SOURCE:
        user.refresh_from_db()
        # Get profile for user.
        profile = user.profile
        # Opt out IGC users from whatsapp messages.
        profile.opt_out_of_whatsapp()

    return user_source
