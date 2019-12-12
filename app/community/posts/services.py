from community.posts.models import Post, File, Like


def get_posts():
    return Post.objects.all()


def get_post(pk):
    return Post.objects.get(pk=pk)


def get_likes():
    return Like.objects.all()


def get_post_files(post):
    return File.objects.filter(post=post)
