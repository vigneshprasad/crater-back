from community.comments.models import Comment


def get_comments():
    return Comment.objects.all()


def get_latest_comments():
    return Comment.objects.all()[:2]
