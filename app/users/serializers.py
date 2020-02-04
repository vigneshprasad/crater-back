import logging

import cryptography
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from allauth.account.utils import setup_user_email
from allauth.utils import (email_address_exists)
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_auth import serializers as rest_auth_serializers
from rest_auth.registration import serializers as register_serializers
from rest_framework import serializers, exceptions

from tags.models import CityProxy
from tags.serializers import TagSerializer
from utils import messages
from utils.fields import Base64FileField
from utils.instagram_service import instagram_service
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
    os_id = serializers.CharField(required=False, allow_blank=False)

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
        self.check_device(user)
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

    def check_device(self, user):
        os_id = self.validated_data.get('os_id', '')
        if user and os_id:
            device, created = models.Device.objects.get_or_create(user=user, os_id=os_id)
            if not created:
                device.is_active = True
                device.save()


class UserDetailSerializer(rest_auth_serializers.UserDetailsSerializer):
    city = serializers.PrimaryKeyRelatedField(queryset=CityProxy.objects.all(), required=False)
    pan_card_base64 = Base64FileField(required=False, write_only=True)

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
            'has_services',
            'has_active_subscription',
            'active_subscription_membership',
            'pan_card',
            'pan_card_base64'
        )
        read_only_fields = (
            'full_registered',
            'has_profile',
            'has_bank_details',
            'has_services',
            'phone_number_verified',
            'email_verified',
            'phone_number',
            'role',
            'has_active_subscription',
            'active_subscription_membership'
        )

    def validate(self, attrs):
        pan_card = attrs.pop('pan_card_base64', None)
        if pan_card:
            attrs['pan_card'] = pan_card
        return attrs


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
        return email.strip().lower()

    def save(self):
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
    uuid = serializers.UUIDField(source='user.uuid', required=False)
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
    cover = serializers.PrimaryKeyRelatedField(
        queryset=models.CoverFile.objects.all(), allow_null=True, required=False
    )
    tag_list = TagSerializer(source='tags', many=True, read_only=True)
    work_city_name = serializers.CharField(source='work_city.name', read_only=True)
    cover_thumbnail = serializers.CharField(source='cover.cover_thumbnail', read_only=True, allow_null=True)
    cover_transcoder = serializers.CharField(source='cover.cover_transcoder', read_only=True, allow_null=True)
    cover_file = serializers.FileField(source='cover.file', read_only=True, allow_null=True)


    class Meta:
        model = models.Profile
        fields = (
            'pk',
            'uuid',
            'name',
            'tag_line',
            'photo',
            'cover',
            'cover_file',
            'introduction',
            'focus',
            'additional_information',
            'instagram',
            'is_instagram_set',
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
            'instagram': {'write_only': True},
        }
        read_only_fields = (
            'cover_thumbnail',
            'cover_transcoder',
            'cover_file',
            'is_instagram_set'
        )

    def validate_cover(self, cover):
        user = self.context['request'].user
        if cover not in user.cover_files.all():
            raise serializers.ValidationError(_('Please use your cover file'))
        return cover

    @staticmethod
    def validate_instagram(instagram_code):
        if instagram_code:
            instagram_long_access_token = instagram_service.convert_code_to_long_access_token(instagram_code)
            if not instagram_long_access_token:
                raise serializers.ValidationError(
                    _('Instagram code is not valid')
                )
            return instagram_long_access_token


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
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        allow_blank=True
    )

    @staticmethod
    def validate_email(email):
        if UserModel.objects.filter(email=email):
            raise serializers.ValidationError(
                _('This email is registered')
            )
        return email.lower()


class NewPhoneNumberSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(required=False, allow_blank=False, allow_null=False)

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


class VerifyEmailSerializer(register_serializers.VerifyEmailSerializer):
    key = serializers.CharField()

    @staticmethod
    def validate_key(key):
        emailconfirmation = EmailConfirmationHMAC.from_key(key)
        if not emailconfirmation:
            queryset = EmailConfirmation.objects.all_valid()
            try:
                emailconfirmation = queryset.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                raise serializers.ValidationError(
                    messages.WRONG_VALIDATE_KEY
                )
        return key


class CoverFileSerializer(serializers.ModelSerializer):
    file_base64 = Base64FileField(
        file_formats=['.jpg', '.png', '.tiff', '.bmp',  '.mov', '.mpeg', '.avi', '.mp4', '.3gp', '.mwv', '.flv'],
        allow_null=True,
        required=False,
        write_only=True
    )
    file = serializers.FileField(allow_null=True, required=False)

    class Meta:
        model = models.CoverFile
        fields = [
            'pk',
            'file',
            'file_base64',
        ]

    @staticmethod
    def validate_file(file):
        ext = file.name.split(".")[-1]
        ext_list = ['jpg', 'png', 'tiff', 'bmp',  'mov', 'mpeg', 'avi', 'mp4', '3gp', 'mwv', 'flv']
        if ext not in ext_list:
            raise serializers.ValidationError(
                _(f'File extension not valid. Valid extensions: {ext_list}')
            )
        return file

    def validate(self, attrs):
        file = attrs.get('file')
        file_base64 = attrs.get('file_base64')
        if not (file or file_base64):
            raise serializers.ValidationError(
                {
                    'file': _('This field is required')
                }
            )
        user = self.context['request'].user
        cover_files = user.cover_files.filter(created__date=timezone.now().date())
        if cover_files.count() > 20:
            raise serializers.ValidationError(
                {
                    'file': _('You have to many uploaded files today')
                }
            )
        return attrs

    def create(self, validated_data):
        file_base64 = validated_data.pop('file_base64', [])
        file = validated_data.pop('file', None)
        if file:
            validated_data['file'] = file
        else:
            validated_data['file'] = file_base64
        obj = super().create(validated_data)
        return obj
