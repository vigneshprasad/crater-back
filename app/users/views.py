from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from rest_framework import generics, mixins, viewsets, permissions, status
from rest_framework.response import Response
from . import serializers, models


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login = True
    success_url = reverse_lazy('home')


class ProfileViewSet(mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = serializers.ProfileSerializer
    queryset = models.Profile.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, instance=request.user.profile)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
