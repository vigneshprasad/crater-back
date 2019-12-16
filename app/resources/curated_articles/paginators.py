from rest_framework.pagination import PageNumberPagination


class CuratedArticlePagination(PageNumberPagination):
    page_size = 9
