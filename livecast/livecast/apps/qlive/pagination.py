from rest_framework.pagination import PageNumberPagination


class QLivePagination(PageNumberPagination):
    page_size = 8
