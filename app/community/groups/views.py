from rest_framework import mixins, status
from rest_framework.exceptions import NotFound
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from community.groups.models import Location, Block
from community.groups.serializers import UserGroupSerializer, LocationSerializer, BlockSerializer
from community.groups.services import get_blockers, get_blocked_user


class UserGroupViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = UserGroupSerializer
    queryset = Location.objects.all()
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        serializer = LocationSerializer(self.queryset, many=True)
        return Response(serializer.data)


class BlockViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    serializer_class = BlockSerializer
    queryset = get_blockers()
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        """
        Delete blocked user by blocker
        """
        try:
            blocked = get_blocked_user(kwargs['pk'])
            Block.objects.get(blocked=blocked, blocker=request.user).delete()
        except Block.DoesNotExist:
            raise NotFound
        return Response(status=status.HTTP_204_NO_CONTENT)
