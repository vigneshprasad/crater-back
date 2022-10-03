from rest_framework import serializers

from conversations.multistream import models

from conversations import serializers as conversation_serializers
from users import models as user_models


class MultiStreamItemSerializer(serializers.ModelSerializer):
    category_detail = conversation_serializers.CategorySerializer(source="category", read_only=True)
    host_detail_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.MultiStream
        fields = (
            "id",
            "title",
            "description",
            "category",
            "streams",
            "category_detail",
            "host_detail_list"
        )

    @staticmethod
    def get_host_detail_list(obj):
        ids = list(obj.streams.all().values_list("host", flat=True))
        hosts = user_models.User.objects.filter(pk__in=ids)
        return conversation_serializers.StreamListHostSerializer(hosts, many=True).data
