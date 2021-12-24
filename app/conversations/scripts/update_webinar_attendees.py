from conversations.models import Group


def run_for_multiple_group_ids(group_ids=None, dry_run=True):
    """Update attendees for provided group ids.

    Args:
        group_ids(list): List of group ids for which attendees
            are to update.
        dry_run(bool): If actual action has to be done.

    """
    if not group_ids:
        return

    for group_id in group_ids:
        print("-----")
        print("Adding attendees for group: {}".format(group_id))
        run(group_id=group_id, dry_run=dry_run)
        print("-----")


def run(group_id=None, dry_run=True):
    """Adds old attendees for past streams of the host."""
    if not group_id:
        print("Group id is required.")
        return

    try:
        current_group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        print(f"Group {group_id} does not exist.")
        return

    prev_attendees_list = []
    # Get host's previous groups
    prev_groups = Group.objects.filter(
        host=current_group.host,
        start__lt=current_group.start
    )
    if not prev_groups:
        print(f"Group {group_id} with host {current_group.host} has no previous groups.")
        return

    print("Current Attendees: {}".format(current_group.attendees.count()))

    # Gather previous groups' attendees.
    prev_attendees_list = []
    for group in prev_groups:
        prev_attendees_list += list(group.attendees.all())
        prev_attendees_list = list(set(prev_attendees_list))

    attendees_to_add = list(
        set(prev_attendees_list) - set(list(current_group.attendees.all()))
    )
    print("Attendees to add: {}".format(len(attendees_to_add)))

    if not dry_run:
        # Update current group attendees
        print(f"Updating group {group_id} attendees")
        current_group.attendees.add(*attendees_to_add)
        current_group.save()
        print("Group attendees count after update: ", current_group.attendees.count())
