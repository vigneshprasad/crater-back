from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import views as auth_views, get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_auth.registration.views import VerifyEmailView as DefaultVerifyEmailView
from rest_auth.views import LogoutView as RestLogoutView
from rest_framework import filters
from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from payment import models as payment_models, serializers as payment_serializers
from services import serializers as service_serializers, models as service_models
from utils import messages
from utils.stripe_service import stripe_service
from . import serializers, models, choices
from .forms import AdminSetPasswordForm
from .paginators import Pagination
from .swagger_schemas import referer_email
from .tasks import send_email


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login = True
    form_class = AdminSetPasswordForm
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


class BankDetailViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = payment_serializers.BankDetailsSerializer
    queryset = payment_models.BankDetails.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if hasattr(request.user, 'bank_details') and request.user.bank_details:
            serializer = self.get_serializer(data=request.data, instance=request.user.bank_details, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = request.user
        stripe_token = serializer.validated_data.pop('stripe_token', None)
        if stripe_token:
            amount = 350 if serializer.validated_data['membership'] == 'premium' else 250
            description = f'Initial membership payment for user: {str(self.request.user.pk)}'
            charge = stripe_service.create_token_charge(
                token=serializer.validated_data['stripe_token'],
                amount=amount,
                description=description
            )
            # TODO: Create Transaction
            if serializer.validated_data['remember_card']:
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
        stripe_token = serializer.validated_data.pop('stripe_token', None)
        if serializer.instance:
            stripe_service.update_customer_source(
                serializer.instance.stripe_custome_id,
                stripe_token
            )
        else:
            serializer.validated_data['stripe_customer_id'] = stripe_service.get_customer_id(
                serializer.validated_data['user'],
                stripe_token
            )
        return serializer

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.stripe_customer_id:
            instance.card_data = stripe_service.get_customer_card_data(instance.stripe_customer_id)
        instance.save()


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
    serializer_class = serializers.NewPhoneNumberSerializer

    @action(methods=['post'], detail=False, serializer_class=serializers.NewPhoneNumberSerializer)
    def new_phone_number(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get('phone_number')
        if phone_number:
            request.user.phone_number = phone_number
        request.user.generate_sms_code(commit=False)
        request.user.save()
        if request.user.phone_number:
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

    @action(methods=['post'], detail=False)
    def send_verify_email(self, request):
        request.user.send_verify_email()
        return Response({'status': messages.EMAIL_VERIFY_SUCCESSFULLY_SENT})


class UserServicesViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    serializer_class = service_serializers.UserServicesSerializer
    queryset = service_models.UserServiceInfo.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
        Request example
            {
            'years_of_experience': 'less_1_year',
            'bar_council': 'text',
            'followers': 100,
            'industries': [industry_pk, industry2_pk],
            'services': [
                {
                    'pk': 1, # if pk exists and service with that pk yours server update service
                    'service_type': service_type_pk,
                    'price_type': 'price',
                    'price': 100,
                    'timeline': 60,
                    'revision': 5,
                    'includes': 'test',
                    'attachments': ['1','2'],
                    'questions': ['1','2']

                },
                {
                    'service_type': service_type_pk,
                    'price_type': 'price',
                    'price': 100,
                    'timeline': 60,
                    'revision': 5,
                    'includes': 'test',
                    'attachments': ['1', '2'],
                    'questions': ['1', '2']

                }
            ],
        }
        """
    )
    def create(self, request, *args, **kwargs):
        if hasattr(request.user, 'user_services_info') and request.user.user_services_info:
            serializer = self.get_serializer(data=request.data, instance=request.user.user_services_info, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = request.user
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def get_object(self):
        if self.request.user.role == 'user':
            if hasattr(self.request.user, 'user_services_info') and self.request.user.user_services_info:
                return self.request.user.user_services_info
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        raise NotFound()

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class InvestorServicesViewSet(mixins.CreateModelMixin,
                              mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    serializer_class = service_serializers.InvestorServicesSerializer
    queryset = service_models.InvestorServiceInfo.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if hasattr(request.user, 'investor_services_info') and request.user.investor_services_info:
            serializer = self.get_serializer(
                data=request.data, instance=request.user.investor_services_info, partial=True
            )
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = request.user
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def get_object(self):
        if self.request.user.role == 'investor':
            if hasattr(self.request.user, 'investor_services_info') and self.request.user.investor_services_info:
                return self.request.user.investor_services_info
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        raise NotFound()

    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class NetworkView(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericAPIView):
    serializer_class = serializers.ProfileSerializer
    queryset = models.Profile.objects.filter(
        user__is_approved=True,
        user__is_active=True,
        user__is_staff=False,
        user__is_superuser=False
    ).order_by('name')
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['tags']
    search_fields = ['name']
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)


class RefererEmailView(APIView):

    @swagger_auto_schema(request_body=referer_email)
    def post(self, request):
        uuid = str(request.user.pk)
        fernet = Fernet(settings.FERNET_KEY)
        encrypted_uuid = fernet.encrypt(uuid.encode('ascii'))
        try:
            email = request.data.get('email').strip()
            validate_email(email)
            if not get_user_model().objects.filter(email=email).exists():
                data = {
                    email: {
                        'key': encrypted_uuid.decode("ascii"),
                        'user': str(request.user)
                    }
                }
                send_email.delay(
                    subject=_('Signup invitation'),
                    to=[email],
                    template_name=choices.template_names.get('invite_friend'),
                    content={},
                    merge_vars=data)
            return Response({'detail': _('Verification e-mail sent.')})
        except (ValidationError, AttributeError):
            return Response({'email': _('Email is not valid.')}, status=status.HTTP_400_BAD_REQUEST)


class InvestorsViewSet(mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    queryset = models.User.objects.filter(
        groups__name='Investor',
        bank_details__isnull=False,
        investor_services_info__isnull=False,
        is_active=True,
        is_superuser=False,
        investor_services_info__reach_out=True
    ).order_by('name')

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = Pagination
    # serializer_class = serializers.ProfileSerializer
    serializer_class = service_serializers.ProfessionalSerializer
    filterset_fields = [
        'investor_services_info__kind_of_funding',
        'investor_services_info__companies',
        'profile__work_city'
    ]


class VerifyEmailView(DefaultVerifyEmailView):

    def get_serializer(self, *args, **kwargs):
        return serializers.VerifyEmailSerializer(*args, **kwargs)


class CoverFileViewSet(mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = models.CoverFile.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CoverFileSerializer

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        serializer.save()
