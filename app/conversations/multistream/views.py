from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from conversations.multistream import models, serializers
from users import permissions


class MultiStreamViewSet(
    viewsets.GenericViewSet
):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.MultiStreamItemSerializer
    queryset = models.MultiStream.objects.all()

    @action(
        methods=["GET"],
        detail=True
    )
    def group(self, request, pk, *args, **kwargs):
        """Returns a multistream for group if present."""

        try:
            multistream = models.MultiStream.objects.get(streams__id__in=[pk])
        except (models.MultiStream.DoesNotExist, ValueError):
            return Response({}, status.HTTP_404_NOT_FOUND)

        serialized = self.get_serializer(multistream)
        return Response(serialized.data, status=status.HTTP_200_OK)
