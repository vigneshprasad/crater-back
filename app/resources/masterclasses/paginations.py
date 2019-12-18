from rest_framework.pagination import PageNumberPagination


class MasterClassPagination(PageNumberPagination):
    page_size = 5
