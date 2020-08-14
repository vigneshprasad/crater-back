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
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from payment import models as payment_models, serializers as payment_serializers
from services import serializers as service_serializers, models as service_models
from users import permissions
from utils import messages
from utils.stripe_service import stripe_service
from . import serializers, models, choices
from .forms import AdminSetPasswordForm
from .models import Profile
from .signals import basic_profile_created, service_created, phone_number_verified, referred_friend
from .paginators import Pagination
from .swagger_schemas import referer_email
from .tasks import send_email


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login = True
    form_class = AdminSetPasswordForm
    success_url = reverse_lazy('admin:dashboard_dashboard_changelist')


class ProfileViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = serializers.ProfileSerializer
    queryset = models.Profile.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        created_flag = True
        if hasattr(request.user, 'profile') and request.user.profile:
            serializer = self.get_serializer(data=request.data, instance=request.user.profile, partial=True)
            created_flag = False
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = request.user
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        response = Response(serializers.ProfileSerializer(request.user.profile).data)
        if created_flag:
            basic_profile_created.send(
                sender=self.__class__,
                user=request.user,
                request=request,
                response=response
            )
        return response

    def get_object(self):
        if hasattr(self.request.user, 'profile') and self.request.user.profile:
            return self.request.user.profile
        return None

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        photo = instance.photo
        if not photo:
            photo = instance.photo_url

        if instance:
            serializer = self.get_serializer(instance)
            data = serializer.data
            data['photo'] = photo.url if hasattr(photo, 'url') else photo
            return Response(data)
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
            try:
                self.get_stripe_customer_id(serializer, stripe_token)
            except:
                raise serializers.serializers.ValidationError(
                    {'stripe_token': _('Stripe token is not valid')}
                )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(payment_serializers.BankDetailsSerializer(request.user.bank_details).data)

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
    def get_stripe_customer_id(serializer, stripe_token):
        if serializer.instance:
            stripe_service.update_customer_source(
                serializer.instance.stripe_customer_id,
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
            request.user.new_phone_number = phone_number
            request.user.generate_sms_code(commit=False)
            request.user.save()
            request.user._send_sms(
                phone_number,
                messages.PHONE_CODE_VERIFICATION.format(code=request.user.sms_code)
            )
        return Response({'status': messages.PHONE_CODE_SUCCESSFULLY_SENT})

    @action(methods=['post'], detail=False, serializer_class=serializers.CheckCodeSerializer)
    def check_sms_code(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.sms_code = ''
        if request.user.new_phone_number:
            phone_number_verified.send(
                sender=self.__class__,
                user=request.user,
                request=request
            )
            request.user.phone_number = request.user.new_phone_number
            request.user.new_phone_number = ''
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
        created_flag = True
        if hasattr(request.user, 'user_services_info') and request.user.user_services_info:
            serializer = self.get_serializer(data=request.data, instance=request.user.user_services_info, partial=True)
            created_flag = False
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = request.user
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        response = Response(service_serializers.UserServicesSerializer(request.user.user_services_info).data)
        if created_flag:
            service_created.send(
                sender=self.__class__,
                user=request.user,
                request=request,
                response=response
            )
        return response



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
        return Response(service_serializers.InvestorServicesSerializer(request.user.investor_services_info).data)

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
    pagination_class = Pagination
    queryset = models.Profile.objects.select_related('user').filter(
        user__is_staff=False,
        user__is_superuser=False,
        user__is_approved=True,
        public_profile=True
    ).order_by('name')
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['tags']
    search_fields = ['name']
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        photo = instance.photo
        if not photo:
            photo = instance.photo_url

        if instance:
            serializer = self.get_serializer(instance)
            data = serializer.data
            data['photo'] = photo.url if hasattr(photo, 'url') else photo
            return Response(data)
        raise NotFound()


    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk:
            try:
                self.kwargs['pk'] = get_user_model().objects.get(pk=pk).profile.pk
                return self.retrieve(request, *args, **kwargs)
            except (get_user_model().DoesNotExist, ValidationError, Profile.DoesNotExist):
                raise NotFound()
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
            if get_user_model().objects.filter(email=email).exists():
                return Response({'email': _('Email already exists.')}, status=status.HTTP_400_BAD_REQUEST)
            data = {
                email: {
                    'key': encrypted_uuid.decode("ascii"),
                    'user': str(request.user),
                    'front_url': settings.FRONT_URL
                }
            }
            send_email.delay(
                subject=_('Signup invitation'),
                to=[email],
                template_name=choices.template_names.get('invite_friend'),
                content={},
                merge_vars=data)
            referred_friend.send(
                sender=self.__class__,
                user=request.user,
                request=request
            )
            return Response({'detail': _('Verification e-mail sent.'), 'email': email})
        except (ValidationError, AttributeError):
            return Response({'email': _('Email is not valid.')}, status=status.HTTP_400_BAD_REQUEST)


class InvestorsViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    queryset = models.User.objects.select_related('profile').filter(
        groups__name='Investor',
        # bank_details__isnull=False,
        investor_services_info__isnull=False,
        is_active=True,
        is_superuser=False,
        investor_services_info__reach_out=True,
        is_approved=True,
        profile__public_profile=True
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

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.User.objects.none()
        return self.queryset.exclude(pk=self.request.user.pk)


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
