import mimetypes

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
    photo = serializers.CharField(source='sender.profile.photo.url', allow_null=True)

    class Meta:
        model = Message
        fields = [
            'message',
            'file',
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
    def get_file_format(message):
        return mimetypes.guess_type(message.file.name)[0] if message.file else None


class UserChatSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['pk', 'name', 'photo', 'is_starred', 'latest_message']

    def get_is_starred(self, user):
        return user.user_stars.filter(creator_id=self.context['user']).exists()

    def get_latest_message(self, user):
        request_user = self.context['user']
        return MessageSerializer(
            instance=Message.objects.filter(
                Q(receiver=user, sender=request_user) | Q(receiver=request_user, sender=user), is_support=False).last()
        ).data

    def get_photo(self, user):
        try:
            if hasattr(user, 'profile') and hasattr(user.profile, 'photo'):
                return user.profile.photo.url
        except ValueError:
            return
