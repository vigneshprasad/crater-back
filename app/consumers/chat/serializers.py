import mimetypes
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from pytz import timezone
from rest_framework import serializers
from consumers.chat.models import Message

tz = timezone(settings.TIME_ZONE)


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.name')
    receiver = serializers.CharField(source='receiver.name', allow_null=True)
    sender_id = serializers.CharField(source='sender.pk', allow_null=True)
    receiver_id = serializers.CharField(source='receiver.pk', allow_null=True)
    created = serializers.SerializerMethodField()
    file_format = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'message',
            'file',
            'filename',
            'file_format',
            'sender',
            'receiver',
            'is_read',
            'pk',
            'photo',
            'created',
            'sender_id',
            'receiver_id',
            'is_support'
        ]

    @staticmethod
    def get_created(message):
        return message.created.astimezone(tz)

    @staticmethod
    def get_filename(message):
        if message.file:
            return os.path.basename(message.file.name)

    @staticmethod
    def get_file_format(message):
        return mimetypes.guess_type(message.file.name)[0] if message.file else None

    @staticmethod
    def get_photo(message):
        try:
            if not hasattr(message.sender, 'profile'):
                return None
            return message.sender.profile.photo.url \
                if message.sender.profile.photo else message.sender.profile.photo_url
        except ValueError:
            return


class UserChatSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()
    last_seen = serializers.DateTimeField(source='last_chat_activity.modified', read_only=True)

    class Meta:
        model = get_user_model()
        fields = ['pk', 'name', 'photo', 'is_starred', 'latest_message', 'last_seen']

    def get_is_starred(self, user):
        return user.user_stars.filter(creator_id=self.context['user']).exists()

    def get_latest_message(self, user):
        request_user = self.context['user']
        message = Message.objects.filter(
                Q(receiver=user, sender=request_user) | Q(receiver=request_user, sender=user), is_support=False
        ).last()
        if message:
            return MessageSerializer(instance=message).data

    def get_photo(self, user):
        try:
            if not hasattr(user, 'profile'):
                return None
            return user.profile.photo.url if user.profile.photo else user.profile.photo_url
        except ValueError:
            return
