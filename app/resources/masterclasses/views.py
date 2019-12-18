from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from resources.masterclasses.models import MasterClass
from resources.masterclasses.paginations import MasterClassPagination
from resources.masterclasses.serializers import MasterClassSerializer


class MaterClassViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = MasterClassSerializer
    queryset = MasterClass.objects.all()
    permission_classes = (IsAuthenticated,)
    pagination_class = MasterClassPagination
    filterset_fields = ['tags']
