import logging
import cryptography

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailConfirmation
from allauth.account.models import EmailConfirmationHMAC
from allauth.account.utils import setup_user_email
from allauth.socialaccount.helpers import complete_social_login
from allauth.utils import email_address_exists
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from phonenumber_field.serializerfields import PhoneNumberField
from requests.exceptions import HTTPError
from rest_auth import serializers as rest_auth_serializers
from rest_auth.registration import serializers as register_serializers
from rest_framework import exceptions
from rest_framework import serializers
from django.contrib.auth.models import Group

from base import serializers as base_serializers
from tags import models as tag_models
from tags import serializers as tag_serializers

from utils import messages
from utils import fields
from utils.instagram_service import instagram_service
from users import models
from users import constants
from users import validators
from users import signals
from users import services
from wn_analytics import models as wn_analytics_models
from conversations import models as conversations_models


logger = logging.getLogger("django.request")
logger.setLevel(logging.ERROR)


class UserGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = (
            "name",
            "pk"
        )


class LoginSerializer(rest_auth_serializers.LoginSerializer):
    username = None
    email = serializers.EmailField(
        required=True,
        error_messages={
            "blank": _("Please enter your email"),
            "invalid": _("Please enter a valid email"),
            "max_length": _("Please enter a valid email"),
        },
        max_length=100
    )
    password = serializers.CharField(
        style={"input_type": "password"},
        error_messages={
            "blank": _("Please enter the password"),
            "min_length": _("Password should have 8 or more symbols")
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
        os_id = attrs.get("os_id", "")
        user = attrs.get("user", "")
        if user and os_id:
            device, created = models.Device.objects.get_or_create(user=user, os_id=os_id)
            if not created:
                device.is_active = True
                device.save()

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")

        user = None

        if "allauth" in settings.INSTALLED_APPS:
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
                    username = get_user_model().objects.get(email__iexact=email).get_username()
                except get_user_model().DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, "", password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _("User account is disabled.")
                raise exceptions.ValidationError(msg)
            # if not user.email_verified:
            #     msg = _("Please  confirm your e-mail first.")
            #     raise exceptions.ValidationError(msg)
        else:
            msg = _("Email or password is not correct")
            raise exceptions.ValidationError(msg)

        # If required, is the email verified?
        if "rest_auth.registration" in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise serializers.ValidationError(_("E-mail is not verified."))

        attrs["user"] = user
        self.check_device(attrs)
        return attrs


class RegisterSerializer(register_serializers.RegisterSerializer):
    username = None
    name = serializers.CharField(
        max_length=100,
        error_messages={
            "blank": _("Please enter your name"),
            "max_length": _("Please enter the valid name"),
        },
    )
    password = serializers.CharField(
        style={"input_type": "password"},
        error_messages={
            "blank": _("Please enter the password"),
            "min_length": _("Password should have 8 or more symbols")
        },
        min_length=8,
        max_length=128,
        validators=[validators.password_validate_symbols]
    )
    email = serializers.EmailField(
        required=True,
        error_messages={
            "blank": _("Please enter your email"),
            "invalid": _("Please enter a valid email"),
            "max_length": _("Please enter a valid email"),
        },
        max_length=100
    )
    intent = serializers.ChoiceField(
        choices=constants.INTENT_CHOICES,
        default=constants.INTENT_NETWORK
    )
    utm_campaign = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    utm_source = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    role = serializers.ChoiceField(
        choices=(
            ("user", "User"),
            ("investor", "Investor")
        ),
        default="user"
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
            "username": self.validated_data.get("username", ""),
            "password1": self.validated_data.get("password", ""),
            "email": self.validated_data.get("email", ""),
            "utm_source": self.validated_data.get("utm_source", None),
            "utm_campaign": self.validated_data.get("utm_campaign", None),
            "name": self.validated_data.get("name", None)
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self, commit=False)
        self.custom_signup(request, user)
        utm_source = self.cleaned_data.get("utm_source")
        utm_campaign = self.cleaned_data.get("utm_campaign")
        name = self.cleaned_data.get("name")
        if name:
            name_list = name.split()
            first_name = name[0]
            last_name = name[1:]
            user.first_name = name_list[0]
            user.last_name = " ".join(name_list[1:])
        user.save()
        if utm_source or utm_campaign:
            wn_analytics_models.UserSource.objects.create(
                user=user,
                utm_source=utm_source,
                utm_campaign=utm_campaign
            )
        self.add_to_group(user)
        self.check_device(user)
        # Adding each user to worknetwork group.
        self.add_to_worknetwork_group(user)
        setup_user_email(request, user, [])
        return user

    def custom_signup(self, request, user):
        name = self.validated_data.get("name")
        user.set_name(name)

    def add_to_group(self, user):
        role = self.validated_data.get("role", "user")
        try:
            group = auth_models.Group.objects.get(name=role.capitalize())
            user.groups.add(group)
        except auth_models.Group.DoesNotExist:
            pass

    def _get_referer(self):
        try:
            code = self.validated_data.get("referer")
            fernet = cryptography.fernet.Fernet(settings.FERNET_KEY)
            uuid = fernet.decrypt(code.encode("ascii")).decode("ascii")
            return get_user_model().objects.get(uuid=uuid)
        except (cryptography.fernet.InvalidToken, AttributeError):
            return None

    def _get_intent(self):
        return self.validated_data.get("intent", constants.INTENT_NETWORK)

    def check_device(self, user):
        os_id = self.validated_data.get("os_id", "")
        if user and os_id:
            device, created = models.Device.objects.get_or_create(user=user, os_id=os_id)
            if not created:
                device.is_active = True
                device.save()

    @staticmethod
    def add_to_worknetwork_group(user):
        """Add users to worknetwork group."""
        worknetwork_group, _ = auth_models.Group.objects.get_or_create(
            name=constants.WORKNETWORK_GROUP
        )
        user.groups.add(worknetwork_group)


class UserDetailSerializer(rest_auth_serializers.UserDetailsSerializer):

    photo = serializers.SerializerMethodField()
    linkedin_url = serializers.URLField(
        source="profile.linkedin_url",
        read_only=True,
        default=None
    )

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "photo",
            "email",
            "name",
            "phone_number",
            "linkedin_url"
        )

    @staticmethod
    def get_photo(obj):
        if not hasattr(obj, "profile"):
            return None
        return obj.profile.photo.url if obj.profile.photo else obj.profile.photo_url

    def update(self, instance, validated_data):
        old_email = instance.email
        super().update(instance, validated_data)
        new_email = instance.email
        if old_email != new_email:
            instance.refresh_auth_secret_key()

        # Update first name and last name of the user.
        name = validated_data.get("name")
        instance.set_name(name)
        instance.save()
        return instance


class PasswordChangeSerializer(rest_auth_serializers.PasswordChangeSerializer):
    new_password = serializers.CharField(
        style={"input_type": "password"},
        error_messages={
            "blank": _("Please enter the password"),
            "min_length": _("Password should have 8 or more symbols")
        },
        min_length=8,
        max_length=128,
        validators=[validators.password_validate_symbols]
    )
    new_password1 = None
    new_password2 = None

    def validate(self, attrs):
        self.set_password_form = self.set_password_form_class(
            user=self.user,
            data={
                "new_password1": attrs.get("new_password"),
                "new_password2": attrs.get("new_password"),
                "old_password": attrs.get("old_password")
            }
        )

        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs


class PasswordResetSerializer(rest_auth_serializers.PasswordResetSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "blank": _("Please enter your email"),
            "invalid": _("Please enter a valid email"),
            "max_length": _("Please enter a valid email"),
        },
        max_length=100
    )
    password_reset_form_class = rest_auth_serializers.PasswordResetSerializer.password_reset_form_class

    def validate_email(self, email):
        return email.strip().lower()

    def save(self):
        email = self.validated_data.get("email")
        try:
            user = get_user_model().objects.get(email=email)
            user.send_reset_password_email()
        except get_user_model().DoesNotExist:
            pass


class PasswordResetConfirmSerializer(rest_auth_serializers.PasswordResetConfirmSerializer):
    new_password = serializers.CharField(
        style={"input_type": "password"},
        error_messages={
            "blank": _("Please enter the password"),
            "min_length": _("Password should have 8 or more symbols")
        },
        validators=[validators.password_validate_symbols],
        min_length=8,
        max_length=128
    )
    new_password1 = None
    new_password2 = None

    def validate(self, attrs):
        attrs.update(
            {
                "new_password1": attrs.get("new_password"),
                "new_password2": attrs.get("new_password")
            }
        )
        return super().validate(attrs)


class ProfileChoiceSerializer(serializers.ChoiceField):

    def to_representation(self, value):
        if not value:
            return None
        return {
            "name": self._choices[value],
            "value": value
        }


class ProfileSerializer(serializers.ModelSerializer):

    uuid = serializers.UUIDField(source="user.uuid", required=False)
    name = serializers.CharField(
        source="user.name",
        required=False,
        error_messages={
            "max_length": _("Invalid name"),
        },
        max_length=100
    )
    email = serializers.CharField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    introduction = serializers.CharField(
        max_length=800,
        error_messages={
            "max_length": _("Max symbols exceeded"),
        },
        allow_blank=True,
        allow_null=True,
        required=False
    )
    photo = fields.Base64FileField(file_formats=[".jpg", ".png", ".tiff", ".bmp"], allow_null=True, required=False)
    photo_url = serializers.URLField(allow_null=True, required=False, allow_blank=True)
    cover = serializers.PrimaryKeyRelatedField(
        queryset=models.CoverFile.objects.all(), allow_null=True, required=False
    )
    tag_list = tag_serializers.TagSerializer(
        source="new_tag",
        many=True,
        read_only=True,
        allow_null=True,
        required=False
    )
    cover_transcoder = serializers.CharField(source="cover.cover_transcoder", read_only=True, allow_null=True)
    cover_file = serializers.FileField(source="cover.file", read_only=True, allow_null=True)
    is_cover_video = serializers.SerializerMethodField()
    cover_thumbnail = serializers.SerializerMethodField()

    can_connect = serializers.SerializerMethodField(read_only=True)

    # TODO(Nishant): Move to this later completely.
    years_of_experience_detail = ProfileChoiceSerializer(
        source="years_of_experience",
        read_only=True,
        choices=models.Profile.YEARS_OF_EXPERIENCE_CHOICES
    )
    education_level_detail = ProfileChoiceSerializer(
        source="education_level",
        read_only=True,
        choices=models.Profile.EDUCATION_LEVEL_CHOICES
    )
    company_type_detail = ProfileChoiceSerializer(
        source="company_type",
        read_only=True,
        choices=models.Profile.COMPANY_TYPE_CHOICES
    )
    company_type_advised_detail = ProfileChoiceSerializer(
        source="company_type_advised",
        read_only=True,
        choices=models.Profile.COMPANY_TYPE_CHOICES
    )
    sector_detail = ProfileChoiceSerializer(
        source="sector",
        read_only=True,
        choices=models.Profile.SECTOR_CHOICES
    )
    number_of_employees_detail = ProfileChoiceSerializer(
        source="number_of_employees",
        read_only=True,
        choices=models.Profile.NUMBER_OF_EMPLOYEE_CHOICES
    )
    project_type_detail = ProfileChoiceSerializer(
        source="project_type",
        read_only=True,
        choices=models.Profile.PROJECT_TYPE_CHOICES
    )
    stage_of_company_detail = ProfileChoiceSerializer(
        source="stage_of_company",
        read_only=True,
        choices=models.Profile.STAGE_OF_COMPANY_CHOICES
    )
    companies_invested_detail = ProfileChoiceSerializer(
        source="companies_invested",
        read_only=True,
        choices=models.Profile.COMPANIES_INVESTED_CHOICES
    )
    groups = UserGroupSerializer(source="user.groups", read_only=True, many=True)
    is_creator = serializers.BooleanField(source="user.is_creator", read_only=True)

    class Meta:
        model = models.Profile
        fields = (
            "pk",
            "uuid",
            "name",
            "email",
            "phone_number",
            "photo",
            "photo_url",
            "cover",
            "cover_file",
            "introduction",
            "linkedin_url",
            "twitter",
            "instagram",
            "tag_list",
            "cover_thumbnail",
            "cover_transcoder",
            "is_cover_video",

            "education_level",
            "years_of_experience",
            "company_type",
            "sector",
            "number_of_employees",
            "project_type",
            "stage_of_company",
            "aspiration",
            "company_type_advised",
            "companies_invested",
            "other_tag",
            "allow_meeting_request",
            "can_connect",
            "primary_url",
            "years_of_experience_detail",
            "education_level_detail",
            "company_type_detail",
            "company_type_advised_detail",
            "sector_detail",
            "number_of_employees_detail",
            "project_type_detail",
            "stage_of_company_detail",
            "companies_invested_detail",
            "is_creator",
            "groups"
        )
        extra_kwargs = {
            "tags": {"write_only": True, "allow_null": True, "required": False}
        }
        read_only_fields = (
            "cover_thumbnail",
            "cover_transcoder",
            "cover_file",
            "is_cover_video",
        )

    def validate_cover(self, cover):
        user = self.context["request"].user
        if cover:
            if cover not in user.cover_files.all():
                raise serializers.ValidationError(_("Please use your cover file"))
        return cover

    @staticmethod
    def get_is_cover_video(obj):
        if not obj.cover:
            return False

        cover_file = obj.cover.file
        ext = cover_file.url.split(".")[-1]
        if ext not in ["mov", "mpeg", "avi", "mp4", "3gp", "mwv", "flv"]:
            return False

        return True

    @classmethod
    def get_cover_thumbnail(cls, profile):
        if not profile.cover:
            return None

        if profile.cover.cover_thumbnail:
            return profile.cover.cover_thumbnail
        if not cls.get_is_cover_video(profile):
            return profile.cover.file.url

    def get_can_connect(self, profile):
        """Returns boolean if the request user can request a
            connection request with the profile user.

        """
        request = self.context.get("request")
        if not request:
            return profile.allow_meeting_request

        user = request.user

        if not user or user.is_anonymous:
            return profile.allow_meeting_request

        # If the request user and profile user are the same,
        # return False
        if user == profile.user:
            return False

        # If the user has not allowed meeting request
        # don't show connect button.
        if not profile.allow_meeting_request:
            return False

        # If the requesting user's score is less than
        # the current profile user's score, don't allow
        # connection request.
        if user.score < profile.user.score:
            return False

        return True

    def update(self, instance, validated_data):

        # Adding user group to investor if investor tag is selected.
        user_tags = validated_data.get("tags") if validated_data.get("tags") else []
        if len(user_tags) > 0:
            instance.new_tag.clear()
            instance.new_tag.add(user_tags[0])
        super().update(instance, validated_data)

        user = instance.user
        name = validated_data.get("name")
        user.set_name(name)

        return instance

    def create(self, validated_data):

        # Adding user group to investor if investor tag is selected.
        user_tags = validated_data.get("tags") if validated_data.get("tags") else []
        profile = super().create(validated_data)

        if len(user_tags) > 0:
            profile.new_tag.clear()
            profile.new_tag.add(user_tags[0])

        profile.save()

        user = profile.user
        name = validated_data.get("name")
        user.set_name(name)

        return profile


class LogoutSerializer(serializers.Serializer):
    os_id = serializers.CharField(required=False, allow_blank=False, allow_null=True)


class SocialLoginSerializer(register_serializers.SocialLoginSerializer):
    os_id = serializers.CharField(required=False, allow_blank=False)
    intent = serializers.ChoiceField(
        choices=constants.INTENT_CHOICES,
        required=False, 
        allow_null=True
    )
    utm_campaign = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    utm_source = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    role = serializers.ChoiceField(
        choices=(
            ("user", "User"),
            ("investor", "Investor")
        ),
        default="user"
    )
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    name = serializers.CharField(
        max_length=255,
        allow_null=True,
        allow_blank=True,
        required=False
    )

    @staticmethod
    def validate_email(email):
        if get_user_model().objects.filter(email=email):
            raise serializers.ValidationError(
                _("This email is registered")
            )
        return email.lower()


class AppleSocialLoginSerializer(SocialLoginSerializer):
    is_web = serializers.BooleanField(default=False)

    def get_social_login(self, adapter, app, token, response):
        """
        :param adapter: allauth.socialaccount Adapter subclass.
            Usually OAuthAdapter or Auth2Adapter
        :param app: `allauth.socialaccount.SocialApp` instance
        :param token: `allauth.socialaccount.SocialToken` instance
        :param response: Provider"s response for OAuth1. Not used in the
        :returns: A populated instance of the
            `allauth.socialaccount.SocialLoginView` instance
        """
        request = self._get_request()
        is_web = self.initial_data.get("is_web", False)
        social_login = adapter.complete_login(request, app, token, response=response, is_web=is_web)
        social_login.token = token
        return social_login

    def validate(self, attrs):
        view = self.context.get("view")
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(
                _("View is not defined, pass it as a context variable")
            )

        adapter_class = getattr(view, "adapter_class", None)
        if not adapter_class:
            raise serializers.ValidationError(_("Define adapter_class in view"))

        adapter = adapter_class(request)
        app = adapter.get_provider().get_app(request)

        # More info on code vs access_token
        # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token

        # Case 1: We received the access_token
        if attrs.get("access_token"):
            access_token = attrs.get("access_token")

        # Case 2: We received the authorization code
        elif attrs.get("code"):
            self.callback_url = getattr(view, "callback_url", None)
            self.client_class = getattr(view, "client_class", None)

            if not self.callback_url:
                raise serializers.ValidationError(
                    _("Define callback_url in view")
                )
            if not self.client_class:
                raise serializers.ValidationError(
                    _("Define client_class in view")
                )

            code = attrs.get("code")

            provider = adapter.get_provider()
            scope = provider.get_scope(request)
            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope
            )
            token = client.get_access_token(code)
            access_token = token["access_token"]

        else:
            raise serializers.ValidationError(
                _("Incorrect input. access_token or code is required."))

        social_token = adapter.parse_token({"access_token": access_token})
        social_token.app = app

        try:
            login = self.get_social_login(adapter, app, social_token, access_token)
            complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_("Incorrect value"))

        if not login.is_existing:
            # We have an account already signed up in a different flow
            # with the same email address: raise an exception.
            # This needs to be handled in the frontend. We can not just
            # link up the accounts due to security constraints
            if allauth_settings.UNIQUE_EMAIL:
                # Do we have an account already with this email address?
                if login.user.email:
                    account_exists = get_user_model().objects.filter(
                        email=login.user.email,
                    ).exists()
                    if account_exists:
                        raise serializers.ValidationError(
                            _("User is already registered with this e-mail address.")
                        )
                else:
                    login.user.email = None

            login.lookup()
            login.save(request, connect=True)

        attrs["user"] = login.account.user

        return attrs


class ConnectSerializer(register_serializers.SocialConnectSerializer):

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = self.context["request"].user
        if attrs["user"] != user:
            raise serializers.ValidationError(
                _("User with that social account already registered")
            )
        return attrs


class NewPhoneNumberSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField(required=False, allow_blank=False, allow_null=False)

    class Meta:
        model = get_user_model()

        fields = [
            "phone_number"
        ]


class CheckCodeSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(max_length=4, min_length=4)

    class Meta:
        model = get_user_model()
        fields = [
            "sms_code",
        ]

    def validate_sms_code(self, code):
        user = self.context["request"].user
        if user.sms_code != code:
            raise serializers.ValidationError(
                messages.PHONE_CODE_WRONG
            )


class VerifyEmailSerializer(register_serializers.VerifyEmailSerializer):
    key = serializers.CharField()

    def validate_key(self, key):
        emailconfirmation = EmailConfirmationHMAC.from_key(key)
        if not emailconfirmation:
            queryset = EmailConfirmation.objects.all_valid()
            try:
                emailconfirmation = queryset.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                raise serializers.ValidationError(
                    messages.WRONG_VALIDATE_KEY
                )
        signals.email_verified.send(
            sender=self.__class__,
            email_address=emailconfirmation.email_address
        )
        return key


class CoverFileSerializer(serializers.ModelSerializer):
    file_base64 = fields.Base64FileField(
        file_formats=[".jpg", ".png", ".tiff", ".bmp",  ".mov", ".mpeg", ".avi", ".mp4", ".3gp", ".mwv", ".flv"],
        allow_null=True,
        required=False,
        write_only=True
    )
    file = serializers.FileField(allow_null=True, required=False)

    class Meta:
        model = models.CoverFile
        fields = [
            "pk",
            "file",
            "file_base64",
        ]

    @staticmethod
    def validate_file(file):
        ext = file.name.split(".")[-1]
        ext_list = ["jpg", "png", "tiff", "bmp",  "mov", "mpeg", "avi", "mp4", "3gp", "mwv", "flv"]
        if ext not in ext_list:
            raise serializers.ValidationError(
                _(f"File extension not valid. Valid extensions: {ext_list}")
            )
        return file

    def validate(self, attrs):
        file = attrs.get("file")
        file_base64 = attrs.get("file_base64")
        if not (file or file_base64):
            raise serializers.ValidationError(
                {
                    "file": _("This field is required")
                }
            )
        user = self.context["request"].user
        cover_files = user.cover_files.filter(created__date=timezone.now().date())
        if cover_files.count() > 20:
            raise serializers.ValidationError(
                {
                    "file": _("You have to many uploaded files today")
                }
            )
        return attrs

    def create(self, validated_data):
        file_base64 = validated_data.pop("file_base64", [])
        file = validated_data.pop("file", None)
        if file:
            validated_data["file"] = file
        else:
            validated_data["file"] = file_base64
        obj = super().create(validated_data)
        return obj


class ProfileExtraInfoMetaSerializer(serializers.ModelSerializer):
    meta = serializers.SerializerMethodField()

    class Meta:
        model = models.ProfileExtraInfoMeta
        fields = (
            "tag",
            "question",
            "meta",
        )

    @staticmethod
    def get_meta(meta):
        return {
            "education_level": services.get_education_level_field_info(),
            "years_of_experience": services.get_years_of_experience_field_info(),
            "company_type": services.get_company_type_field_info(),
            "sector": services.get_sector_field_info(),
            "name": services.get_name_field_info(),
            "number_of_employees": services.get_number_of_employees_field_info(),
            "project_type": services.get_project_type_field_info(),
            "stage_of_company": services.get_stage_of_company_field_info(),
            "aspiration": services.get_aspiration_field_info(),
            "company_name": services.get_company_name_field_info(),
            "company_type_advised": services.get_company_type_advised_field_info(),
            "companies_invested": services.get_companies_invested_field_info(),
            "other_tag": services.get_other_tag_field_info(),
        }


class UserReferralStreamSerializer(serializers.ModelSerializer):
    topic = serializers.StringRelatedField(source="topic.name", read_only=True)

    class Meta:
        model = conversations_models.Group
        fields = (
            "id",
            "topic",
            "start",
        )


class UserReferralSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.name", read_only=True)
    referrer = serializers.CharField(source="referrer.name", read_only=True)
    stream_detail = UserReferralStreamSerializer(source="stream", read_only=True)
    status = base_serializers.DisplayChoiceField(
        read_only=True,
        choices=models.UserReferral.USER_REFERRAL_STATUS_CHOICES
    )

    class Meta:
        model = models.UserReferral
        fields = (
            "id",
            "user",
            "referrer",
            "amount",
            "status",
            "stream_detail",
        )
        read_only_fields = fields


class UserPermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UserPermission
        fields = (
            "id",
            "user",
            "allow_create_stream",
            "allow_chat"
        )