from django.core.exceptions import ValidationError
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from order.models import Order
from order.serializers import ReviewSerializer
from users import permissions
from users.models import User
from . import models, serializers
from .filters import ProfessionalFilter
from .paginators import Pagination, ShortPagination


class CategoryViewSet(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Category.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.CategorySerializer
    filterset_fields = ['direction']
