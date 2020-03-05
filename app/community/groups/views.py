from django.core.exceptions import ValidationError
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from community.groups.models import Location, Block, Following, Group
from community.groups.serializers import UserRequestSerializer, LocationSerializer, BlockSerializer, FollowSerializer, \
    GroupSerializer
from community.groups.services import get_blockers, get_blocked_user, get_followers, get_followed_user


class UserRequestViewSet(mixins.CreateModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = UserRequestSerializer
    queryset = Location.objects.all()
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        serializer = LocationSerializer(
            self.queryset.order_by('order', 'name'), many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated],
        serializer_class=GroupSerializer,
        detail=False
    )
    def my(self, request):
        serializer = self.serializer_class(
            Group.objects.filter(
                group_users__user=self.request.user,
                group_users__is_approved=True), many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['get'],
        permission_classes=[IsAuthenticated],
        serializer_class=GroupSerializer,
        detail=True
    )
    def approved(self, request, pk):
        is_approved = Group.objects.prefetch_related('group_users').filter(
            pk=pk,
            group_users__user=request.user,
            group_users__is_approved=True
        ).exists()
        is_requested = Group.objects.prefetch_related('group_users').filter(
            pk=pk,
            group_users__user=request.user,
        ).exists()
        return Response({'approved': is_approved, 'requested': is_requested})


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
        except (Block.DoesNotExist, ValidationError):
            raise NotFound
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
    serializer_class = FollowSerializer
    queryset = get_followers()
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        """
        Delete followed user by follower
        """
        data = {}
        try:
            followed = get_followed_user(kwargs['pk'])
            follow = Following.objects.get(followed=followed, follower=request.user)
            # Front end developers requirements. Can`t do anything without this data
            data = self.get_serializer(follow).data
            follow.delete()
        except Following.DoesNotExist:
            raise NotFound
        return Response(status=status.HTTP_200_OK, data=data)
