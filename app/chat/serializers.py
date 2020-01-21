from rest_framework import serializers

from chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.name')
    receiver = serializers.CharField(source='receiver.name', allow_null=True)

    class Meta:
        model = Message
        fields = ['message', 'file', 'sender', 'receiver',  'is_read', 'pk', 'created']
