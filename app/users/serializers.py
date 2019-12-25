import logging

import cryptography
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import (email_address_exists)
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
from rest_auth import serializers as rest_auth_serializers
from rest_auth.registration import serializers as register_serializers
from rest_framework import serializers, exceptions

from tags.serializers import TagSerializer
from utils import messages
from utils.fields import Base64FileField
from . import models
from .validators import password_validate_symbols

UserModel = get_user_model()

logger = logging.getLogger('django.request')
logger.setLevel(logging.ERROR)


class LoginSerializer(rest_auth_serializers.LoginSerializer):
    username = None
    email = serializers.EmailField(
        required=True,
        error_messages={
            'blank': _('Please enter your email'),
            'invalid': _('Please enter a valid email'),
            'max_length': _('Please enter a valid email'),
        },
        max_length=100
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages={
            'blank': _('Please enter the password'),
            'min_length': _('Password should have 8 or more symbols')
        },
        min_length=8,
        max_length=128
    )
    os_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    @staticmethod
    def validate_email(email):
        return email.strip().lower()

    @staticmethod
    def check_device(attrs):
        os_id = attrs.get('os_id', '')
        user = attrs.get('user', '')
        if user and os_id:
            device, created = models.Device.objects.get_or_create(user=user, os_id=os_id)
            if not created:
                device.is_active = True
                device.save()

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account import app_settings

            # Authentication through email
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL:
                user = self._validate_email(email, password)

            # Authentication through username
            elif app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME:
                user = self._validate_username(username, password)

            # Authentication through either username or email
            else:
                user = self._validate_username_email(username, email, password)

        else:
            # Authentication without using allauth
            if email:
                try:
                    username = UserModel.objects.get(email__iexact=email).get_username()
                except UserModel.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, '', password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Email or password is not correct')
            raise exceptions.ValidationError(msg)

        # If required, is the email verified?
        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise serializers.ValidationError(_('E-mail is not verified.'))

        attrs['user'] = user
        self.check_device(attrs)
        return attrs


class RegisterSerializer(register_serializers.RegisterSerializer):
    username = None
    name = serializers.CharField(
        max_length=100,
        error_messages={
            'blank': _('Please enter your name'),
            'max_length': _('Please enter the valid name'),
        },
    )
    password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages={
            'blank': _('Please enter the password'),
            'min_length': _('Password should have 8 or more symbols')
        },
        min_length=8,
        max_length=128,
        validators=[password_validate_symbols]
    )
    email = serializers.EmailField(
        required=True,
        error_messages={
            'blank': _('Please enter your email'),
            'invalid': _('Please enter a valid email'),
            'max_length': _('Please enter a valid email'),
        },
        max_length=100
    )
    role = serializers.ChoiceField(
        choices=(
            ('user', 'User'),
            ('investor', 'Investor')
        ),
        default='user'
    )
    referer = serializers.CharField(
        required=False,
        max_length=255
    )
    password1 = None
    password2 = None

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("This email is already registered, sign in instead"))
        return email.strip().lower()

    @staticmethod
    def validate_password(password):
        return get_adapter().clean_password(password)

    @staticmethod
    def validate(data):
        return data

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password', ''),
            'email': self.validated_data.get('email', '')
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        user.referer = self._get_referer()
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self, commit=False)
        self.custom_signup(request, user)
        user.save()
        self.add_to_group(user)
        setup_user_email(request, user, [])
        user.send_verify_email()
        return user

    def custom_signup(self, request, user):
        user.name = self.validated_data.get('name')

    def add_to_group(self, user):
        role = self.validated_data.get('role', 'user')
        try:
            group = auth_models.Group.objects.get(name=role.capitalize())
            user.groups.add(group)
        except auth_models.Group.DoesNotExist:
            pass

    def _get_referer(self):
        try:
            code = self.validated_data.get('referer')
            fernet = Fernet(settings.FERNET_KEY)
            uuid = fernet.decrypt(code.encode('ascii')).decode('ascii')
            return get_user_model().objects.get(uuid=uuid)
        except (cryptography.fernet.InvalidToken, AttributeError):
            return None


class UserDetailSerializer(rest_auth_serializers.UserDetailsSerializer):

    class Meta:
        model = UserModel
        fields = (
            'pk',
            'email',
            'email_verified',
            'name',
            'city',
            'reason',
            'phone_number',
            'phone_number_verified',
            'role',
            'full_registered',
            'has_profile',
            'has_bank_details',
            'has_services'
        )
        read_only_fields = (
            'email',
            'full_registered',
            'has_profile',
            'has_bank_details',
            'has_services',
            'phone_number_verified',
            'email_verified',
            'phone_number',
            'role'
        )


class PasswordChangeSerializer(rest_auth_serializers.PasswordChangeSerializer):
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages={
            'blank': _('Please enter the password'),
            'min_length': _('Password should have 8 or more symbols')
        },
        min_length=8,
        max_length=128,
        validators=[password_validate_symbols]
    )
    new_password1 = None
    new_password2 = None

    def validate(self, attrs):
        self.set_password_form = self.set_password_form_class(
            user=self.user,
            data={
                'new_password1': attrs.get('new_password'),
                'new_password2': attrs.get('new_password'),
                'old_password': attrs.get('old_password')
            }
        )

        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs


class PasswordResetSerializer(rest_auth_serializers.PasswordResetSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            'blank': _('Please enter your email'),
            'invalid': _('Please enter a valid email'),
            'max_length': _('Please enter a valid email'),
        },
        max_length=100
    )
    password_reset_form_class = rest_auth_serializers.PasswordResetSerializer.password_reset_form_class

    def validate_email(self, email):
    #     self.reset_form = self.password_reset_form_class(data=self.initial_data)
    #     if not self.reset_form.is_valid():
    #         raise serializers.ValidationError(self.reset_form.errors)
        return email.strip().lower()


    def save(self):
        # request = self.context.get('request')
        # Set some values to trigger the send_email method.
        email = self.validated_data.get('email')
        try:
            user = UserModel.objects.get(email=email)
            user.send_reset_password_email()
        except UserModel.DoesNotExist:
            pass


class PasswordResetConfirmSerializer(rest_auth_serializers.PasswordResetConfirmSerializer):
    new_password = serializers.CharField(
        style={'input_type': 'password'},
        error_messages={
            'blank': _('Please enter the password'),
            'min_length': _('Password should have 8 or more symbols')
        },
        validators=[password_validate_symbols],
        min_length=8,
        max_length=128
    )
    new_password1 = None
    new_password2 = None

    def validate(self, attrs):
        attrs.update(
            {
                'new_password1': attrs.get('new_password'),
                'new_password2': attrs.get('new_password')
            }
        )
        return super().validate(attrs)


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        error_messages={
            'blank': _('Please enter your name'),
            'max_length': _('Invalid name'),
        },
        max_length=100
    )
    tag_line = serializers.CharField(
        error_messages={
            'max_length': _('Tag line should not be longer than 100 symbols'),
        },
        max_length=100,
        allow_blank=True
    )
    introduction = serializers.CharField(
        max_length=800,
        error_messages={
            'max_length': _('Max symbols exceeded'),
        },
        allow_blank=True
    )
    focus = serializers.CharField(
        max_length=800,
        error_messages={
            'max_length': _('Max symbols exceeded'),
        },
        allow_blank=True
    )
    additional_information = serializers.CharField(
        max_length=800,
        error_messages={
            'max_length': _('Max symbols exceeded'),
        },
        allow_blank=True
    )
    photo = Base64FileField(file_formats=['.jpg', '.png', '.tiff', '.bmp'], allow_null=True)
    cover = Base64FileField(
        file_formats=['.jpg', '.png', '.tiff', '.bmp',  '.mov', '.mpeg', '.avi', '.mp4', '.3gp', '.mwv', '.flv'],
        allow_null=True
    )
    tag_list = TagSerializer(source='tags', many=True, read_only=True)
    work_city_name = serializers.CharField(source='work_city.name', read_only=True)

    class Meta:
        model = models.Profile
        fields = (
            'pk',
            'name',
            'tag_line',
            'photo',
            'cover',
            'introduction',
            'focus',
            'additional_information',
            'instagram',
            'twitter',
            'work_city',
            'work_city_name',
            'tags',
            'tag_list',
            'public_profile',
            'cover_thumbnail',
            'cover_transcoder'
        )
        extra_kwargs = {
            'tags': {'write_only': True},
        }
        read_only_fields = (
            'cover_thumbnail',
            'cover_transcoder'
        )


class LogoutSerializer(serializers.Serializer):
    os_id = serializers.CharField(required=False, allow_blank=False, allow_null=True)


class SocialLoginSerializer(register_serializers.SocialLoginSerializer):
    os_id = serializers.CharField(required=False, allow_blank=False)
    role = serializers.ChoiceField(
        choices=(
            ('user', 'User'),
            ('investor', 'Investor')
        ),
        default='user'
    )


class NewPhoneNumberSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel

        fields = [
            'phone_number'
        ]


class CheckCodeSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(max_length=4, min_length=4)

    class Meta:
        model = UserModel
        fields = [
            'sms_code'
        ]

    def validate_sms_code(self, code):
        user = self.context['request'].user
        if user.sms_code != code:
            raise serializers.ValidationError(
                messages.PHONE_CODE_WRONG
            )
