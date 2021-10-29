from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FeaturedWebinarPagination(PageNumberPagination):

    page_size = 5
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ("count", self.page.paginator.count),
            ("current_page", int(self.request.query_params.get("page", 1))),
            ("next", self.get_next_link()),
            ("previous", self.get_previous_link()),
            ("results", data)
        ]))


class WebinarPagination(PageNumberPagination):

    page_size = 5
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ("count", self.page.paginator.count),
            ("current_page", int(self.request.query_params.get("page", 1))),
            ("next", self.get_next_link()),
            ("previous", self.get_previous_link()),
            ("results", data)
        ]))
