from community.comments.models import Comment


def get_comments():
    return Comment.objects.all()


def get_latest_comments():
    return Comment.objects.all()[:2]


def get_comments_without_latest():
    return Comment.objects.all()[2:]
