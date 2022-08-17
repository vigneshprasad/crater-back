from communications.emails import constants, private


def send_email_for_group_analytics_to_creator(group):
    """Sends email about group analytics for recently closed
        group to the host of the group.

    Args:
        group(Group): Stream we are sending analytics email
            for.

    """
    private.send_email_for_user(
        subject="Analytics on your stream are available.",
        to=group.host,
        template_name=constants.CREATOR_STREAM_ANALYTICS_TEMPLATE,
        merge_vars={},
        from_email="hello@worknetwork.in"
    )
