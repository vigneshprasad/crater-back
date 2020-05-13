import copy


class SetCreatorRequestDataMixin:
    request_user = 'user'

    def to_internal_value(self, data):
        """
        Initial transform data for serializer, set creator as request user
        :param data: request data
        """
        try:
            data = copy.deepcopy(data)
        except TypeError:
            pass
        if self.context.get('request'):
            data[self.request_user] = self.context['request'].user.pk
        return super().to_internal_value(data)
