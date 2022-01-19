import copy
from rest_framework import serializers

from crater.payments import models


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Payment
        fields = "__all__"

    def to_internal_value(self, data):
        """
        Initial transform data for serializer, set user as request user
        :param data: request data
        """
        try:
            data = copy.deepcopy(data)
        except TypeError:
            pass
        if self.context.get('request'):
            data["user"] = self.context['request'].user.pk
        return super().to_internal_value(data)
