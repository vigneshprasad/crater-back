from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from rest_framework import mixins, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_auth.views import LogoutView as RestLogoutView
from . import serializers, models


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login = True
    success_url = reverse_lazy('home')


class ProfileViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = serializers.ProfileSerializer
    queryset = models.Profile.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile:
            serializer = self.get_serializer(data=request.data, instance=request.user.profile, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = request.user
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def get_object(self):
        if hasattr(self.request.user, 'profile') and self.request.user.profile:
            return self.request.user.profile
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        raise NotFound()

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class LogoutView(RestLogoutView):
    serializer_class = serializers.LogoutSerializer

    def logout(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        os_id = serializer.validated_data.get('os_id', '')
        if os_id:
            try:
                device = models.Device.objects.get(user=self.request.user, os_id=os_id)
                device.is_active = False
                device.save()
            except models.Device.DoesNotExist:
                pass
        return super().logout(request)
