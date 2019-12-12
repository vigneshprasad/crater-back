from community.groups.models import Group, Block


def get_group(pk):
    return Group.objects.get(pk=pk)


def get_blocked_user(user_pk):
    return Block.objects.get(blocker_id=user_pk).blocked


def get_blockers():
    return Block.objects.all()
