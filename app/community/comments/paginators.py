from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CommentPagination(PageNumberPagination):
    page_size = 5

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count + 2 if self.page.paginator.count else 0),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))
