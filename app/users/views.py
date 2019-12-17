from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from rest_framework import mixins, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_auth.views import LogoutView as RestLogoutView
from rest_framework.decorators import action
from . import serializers, models

from utils import messages
from payment import models as payment_models, serializers as payment_serializers
from utils.stripe_service import stripe_service


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login = True
    success_url = reverse_lazy('home')


class ProfileViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = payment_serializers.BaskDetailsSerializer
    queryset = payment_models.BankDetails.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if hasattr(request.user, 'bank_details') and request.user.bank_details:
            serializer = self.get_serializer(data=request.data, instance=request.user.bank_details, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = request.user
        self.get_stripe_customer_id(serializer)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def get_object(self):
        if hasattr(self.request.user, 'bank_details') and self.request.user.bank_details:
            return self.request.user.bank_details
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        raise NotFound()

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @staticmethod
    def get_stripe_customer_id(serializer):
        stripe_token = serializer.validate_data.get('stripe_token', None)
        if not stripe_token:
            return serializer
        if serializer.instance:
            stripe_service.update_customer_source(
                serializer.instance.stripe_custome_id,
                stripe_token
            )
        else:
            serializer.validate_data['stripe_customer_id'] = stripe_service.get_customer_id(
                serializer.validate_data['user'],
                stripe_token
            )
        return serializer

    def perform_create(self, serializer):
        instance = serializer.save(commit=False)
        instance.card_data = stripe_service.get_customer_card_data(instance.stripe_customer_id)
        instance.save()


class BankDetailViewSet(mixins.CreateModelMixin,
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


class VerificationView(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=['post'], detail=False, serializer_class=serializers.NewPhoneNumberSerializer)
    def new_phone_number(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.phone_number = serializer.validated_data['phone_number']
        request.user.generate_sms_code(commit=False)
        request.user.save()
        request.user.send_sms(
            messages.PHONE_CODE_VERIFICATION.format(code=request.user.sms_code)
        )
        return Response({'status': messages.PHONE_CODE_SUCCESSFULLY_SENT})

    @action(methods=['post'], detail=False, serializer_class=serializers.CheckCodeSerializer)
    def check_sms_code(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.sms_code = ''
        request.user.phone_number_verified = True
        request.user.save()
        return Response({'status': messages.PHONE_NUMBER_SUCCESSFULLY_VERIFIED})
