from community.posts.models import Post, File, Like


def get_community_posts():
    return Post.objects.filter(group__isnull=True).all()


def get_posts():
    return Post.objects.all()


def get_posts_count():
    return Post.objects.count()


def get_post(pk):
    return Post.objects.get(pk=pk)


def get_likes():
    return Like.objects.all()


def get_post_files(post):
    return File.objects.filter(post=post)
