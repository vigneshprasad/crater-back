from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from resources.masterclasses.filter_backends import TagFilterBackend
from resources.masterclasses.models import MasterClass
from resources.masterclasses.paginations import MasterClassPagination
from resources.masterclasses.serializers import MasterClassSerializer
from resources.masterclasses.tasks import masterclass_count_views
from users import permissions


class MaterClassViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = MasterClassSerializer
    queryset = MasterClass.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = MasterClassPagination
    filter_backends = (TagFilterBackend,)

    def retrieve(self, request, *args, **kwargs):
        masterclass_count_views.delay(self.get_object().pk)
        return super().retrieve(request, *args, **kwargs)
