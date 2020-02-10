from rest_framework import serializers
from rest_framework.fields import FileField

from community.comments.serializers import CommentSerializer
from community.mixins import SetCreatorRequestDataMixin
from community.posts.models import Post, File, Like, Report
from community.posts.services import get_post_files
from utils.fields import Base64FileField


class PostSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'creator'

    files_base64 = serializers.ListField(
        required=False, child=Base64FileField(max_length=None, use_url=True)
    )
    files_formdata = serializers.ListField(
        required=False, child=FileField(max_length=None, use_url=True)
    )
    files_urls = serializers.SerializerMethodField()
    files_data = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    my_like = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    is_reported = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    latest_comments = serializers.SerializerMethodField()
    creator_name = serializers.CharField(read_only=True, source='creator.name')
    creator_photo = serializers.ImageField(source='creator.profile.photo', read_only=True)

    class Meta:
        model = Post
        fields = (
            'pk',
            'message',
            'group',
            'files_base64',
            'files_urls',
            'files_data',
            'files_formdata',
            'creator',
            'creator_name',
            'creator_photo',
            'created',
            'likes',
            'my_like',
            'is_followed',
            'is_reported',
            'comments',
            'latest_comments'
        )

    def create(self, validated_data):
        files_json = validated_data.pop('files_base64', [])
        files_formdata = validated_data.pop('files_formdata', [])
        post = super().create(validated_data)
        self._create_post_files(files_json or files_formdata, post)
        return post

    def get_files_urls(self, post):
        return [self.context['request'].build_absolute_uri(file.object.url) for file in get_post_files(post)]

    def get_my_like(self, post):
        return post.likes.filter(user=self.context['request'].user).exists()

    @staticmethod
    def get_files_data(post):
        return [
            {
                'file': post_file.file.cover_transcoder,
                'thumbnail': post_file.file.cover_thumbnail
             }
            for post_file in get_post_files(post) if post_file.file and post_file.file.file
        ]

    @staticmethod
    def _create_post_files(files, post):
        """
        Create post files for base64 data
        """
        if len(files) > 10:
            raise serializers.ValidationError({'files', _('Can\'t be attached more than 10 photos/videos')})
        for file in files:
            File.objects.create(object=file, post=post)

    @staticmethod
    def get_likes(post):
        return post.likes.count()

    @staticmethod
    def get_comments(post):
        return post.comments.count()

    def get_is_followed(self, post):
        return post.creator.follows.filter(follower=self.context['request'].user).exists()

    @staticmethod
    def get_latest_comments(post):
        return CommentSerializer(post.comments.all()[:2], many=True).data

    def get_is_reported(self, post):
        return post.reports.filter(user=self.context['request'].user).exists()


class LimitedPostSerializer(PostSerializer):
    is_my_group = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'pk',
            'message',
            'group',
            'is_my_group',
            'files_base64',
            'files_urls',
            'files_data',
            'files',
            'creator',
            'creator_name',
            'creator_photo',
            'created',
            'likes',
            'comments',
        )

    def get_is_my_group(self, post):
        if not post.group or self.context['request'].user.is_superuser:
            return True
        return post.group.group_users.filter(user=self.context['request'].user, is_approved=True).exists()


class LikeSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'user'

    class Meta:
        model = Like
        fields = (
            'pk',
            'post',
            'user'
        )


class ReportSerializer(SetCreatorRequestDataMixin, serializers.ModelSerializer):
    request_user = 'user'

    class Meta:
        model = Report
        fields = (
            'pk',
            'post',
            'user'
        )
