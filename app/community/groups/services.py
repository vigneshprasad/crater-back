from community.groups.models import Group, Block, Following


def get_group(pk):
    return Group.objects.get(pk=pk)


def get_blocked_user(user_pk):
    return Block.objects.get(blocked_id=user_pk).blocked


def get_blockers():
    return Block.objects.all()


def get_followers():
    return Following.objects.all()


def get_followers_count(pk):
    return Following.objects.filter(followed=pk).count()
