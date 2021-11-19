from conversations.models import Group


def run(group_id=None, dry_run=True):
    if not group_id:
        print("Group id is required.")
        return

    try:
        current_group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        print(f"Group {group_id} does not exist.")
        return

    print("Group attendees count before update: ", current_group.attendees.count())

    # Get host's previous groups
    prev_groups = Group.objects.filter(
        host=current_group.host,
        start__lt=current_group.start
    )
    if not prev_groups:
        print(f"Group {group_id} with host {current_group.host} has no previous groups.")
        return

    # Gather previous groups' attendees
    prev_attendees_list = None
    for group in prev_groups:
        if not prev_attendees_list:
            prev_attendees_list = group.attendees.all()

        prev_attendees_list = prev_attendees_list | group.attendees.all()

    print(f"Updating group {group_id} attendees")

    if not dry_run:
        # Update current group attendees
        current_group.attendees.add(*prev_attendees_list)
        current_group.save()
        print("Group attendees count after update: ", current_group.attendees.count())
