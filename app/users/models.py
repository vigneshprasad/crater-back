import datetime
import uuid

import exrex
from allauth.account.models import EmailAddress, EmailConfirmation
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField

from base import models as base_models
from notifications.models import UserNotificationsSettings
from payment.models import Subscription
from users.managers import UserManager
from utils.user_secret_key import create_new_secret_key
from utils.validators import SizeValidator
from utils.deep_link_service import deep_link_service
from users import constants

# TODO(Nishant) Clean up tasks and move all these tasks to tasks file or don't user models in tasks.
from .tasks import send_twilio_message, send_unique_push, send_email, start_transcoding_for_cover_file


class User(AbstractUser):
    """Extends Abstract User model with additional fields.
        Makes authentication with email and password fields.

    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # TODO(Nishant): Add unique True for username and change the USERNAME_FIELD.
    username = models.CharField(_("Username"), max_length=150)

    email = models.EmailField(_("Email"), unique=True, null=True, blank=True)
    name = models.CharField(_("Name"), max_length=100, null=True, blank=True)

    # TODO(Nishant): If not being used we can remove this.
    city = models.ForeignKey(
        "tags.CityProxy",
        verbose_name=_("City"),
        null=True,
        blank=True,
        related_name="users",
        on_delete=models.SET_NULL
    )

    # TODO(Nishant): No being used remove.
    objectives = models.ManyToManyField(
        "tags.Objective",
        verbose_name=_("Objectives")
    )
    intent = models.CharField(
        verbose_name=_("Intent"),
        max_length=100,
        null=True, 
        blank=True,
        choices=constants.INTENT_CHOICES,
        default=constants.INTENT_NETWORK
    )
    reason = models.CharField(
        max_length=400,
        verbose_name=_("Reason"),
        null=True,
        blank=True
    )
    source = models.CharField(
        max_length=400,
        verbose_name=_("Source"),
        null=True,
        blank=True
    )
    new_source = models.ForeignKey(
        "users.Source",
        related_name="users",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Phone number")
    )
    phone_number_verified = models.BooleanField(
        default=False,
        verbose_name=_("Phone Number Verified")
    )
    new_phone_number = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Phone number")
    )
    sms_code = models.CharField(
        null=True,
        blank=True,
        verbose_name=_("Sms code"),
        max_length=4
    )
    referer = models.ForeignKey(
        "users.User",
        verbose_name=_("Referer"),
        related_name="referrals",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_staff = models.BooleanField(
        _("Admin"),
        default=False,
        help_text=_("Admin permissions, can be restricted by superadmin."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Banned/Unbanned User."
        ),
    )
    is_approved = models.BooleanField(
        _("Approved"),
        default=False,
        help_text=_(
            "User Approval."
        ),
    )
    is_service_approved = models.BooleanField(
        _("Service Approved"),
        default=False,
        help_text=_(
            "User Service Approval."
        ),
    )
    rating = models.FloatField(
        verbose_name=_("Rating"),
        null=True,
        blank=True
    )
    price_start = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Price start")
    )
    pan_card = models.ImageField(
        null=True,
        blank=True,
        verbose_name=_("Pan card"),
        upload_to="user/pan_card/%Y/%m/%d"
    )
    auth_secret_key = models.CharField(
        max_length=255,
        verbose_name=_("Secret key"),
        null=True,
        blank=True
    )
    score = models.PositiveIntegerField(default=0)

    # TODO(Nishant): Change this to username once we can make it unique.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        db_table = "users"
        ordering = ("date_joined",)

    def __str__(self):
        return "{} ({})".format(self.name, self.username)

    @property
    def display_name(self):
        """Return display name for the user."""
        name = self.name.strip() if self.name else self.name
        if not name:
            return None

        return name.title()

    def get_display_first_name(self):
        """Returns first name in title format."""
        first_name = self.first_name.strip() if self.first_name else self.first_name
        if not first_name:
            return self.display_name

        return first_name.title()

    def set_phone_number_verified(self):
        """Marks a users phone number as verified.

        Note:
            For now marking user approved and service approved
                if the user"s phone number is verified.

        """
        self.phone_number_verified = True
        self.is_approved = True
        self.is_service_approved = True
        self.save()

    @staticmethod
    def send_email(
            subject,
            to,
            template_name,
            content,
            merge_vars,
            **kwargs
    ):
        # Update merge vars with Front URL.
        for d in merge_vars.values():
            d.update({"front_url": settings.FRONT_URL})

        send_email.delay(
            subject=subject,
            to=to,
            template_name=template_name,
            content=content,
            merge_vars=merge_vars,
            **kwargs
        )

    def send_reset_password_email(self):
        uid = urlsafe_base64_encode(force_bytes(self.pk))
        token = default_token_generator.make_token(self)
        password_reset_url = "https://{}/auth/new-password?uid={}&token={}".format(settings.FRONT_URL, uid, token)
        deep_link = deep_link_service.make_firebase_deep_link(password_reset_url)
        data = {
            self.email: {
                "reset_password_url": deep_link,
                "name": self.name,
            }
        }

        self.send_email(subject="Password reset", to=[self.email], from_email=constants.PASSWORD_RESET_FROM_EMAIL,
                        template_name=constants.template_names.get("password_reset"), content={},
                        merge_vars=data)

    def get_phone_number(self):
        """Returns phone number string if present."""
        return str(self.phone_number) if self.phone_number else None

    @property
    def has_profile(self):
        """Checking if the user has profile object.

        Note:
            First this function check for the raw object and then
            checks if the profile is saved in the DB. If any of
            these conditions are not met, it returns False.

        """
        has_profile_object = bool(hasattr(self, "profile") and self.profile)
        if not has_profile_object:
            return False
        if not self.profile.pk:
            return False
        return True

    @property
    def has_points(self):
        return bool(hasattr(self, "points") and self.points)

    @property
    def profile_completed(self):
        status = (
            self.has_profile
            and
            self.phone_number
            and
            self.phone_number_verified
            and
            self.email_verified
            and
            self.is_approved
        )
        return status

    @property
    def has_bank_details(self):
        return bool(hasattr(self, "bank_details") and self.bank_details)

    @property
    def has_introduction(self):
        status = (
            self.has_profile
            and 
            hasattr(self.profile, "introduction")
            and 
            self.profile.introduction
        )
        return bool(status)

    @property
    def full_registered(self):
        status = (
            self.has_profile
            and
            self.has_bank_detais
            and
            self.has_services
        )
        return status

    @property
    def has_services(self):
        if self.role == "user":
            return bool(hasattr(self, "user_services_info") and self.user_services_info)
        elif self.role == "investor":
            return bool(hasattr(self, "investor_services_info") and self.investor_services_info)
        return None

    @property
    def has_active_subscription(self):
        return self.subscriptions.filter(is_active=True).exists()

    @property
    def active_subscription_membership(self):
        active_subscription = self.subscriptions.filter(is_active=True).first()
        if active_subscription:
            return active_subscription.membership
        return None

    @property
    def role(self):
        if self.groups.filter(name="Investor").exists():
            return "investor"
        if self.groups.filter(name="User").exists():
            return "user"
        return None

    @staticmethod
    def _send_sms(phone_number, message):
        send_twilio_message.delay(str(phone_number), message)

    def send_sms(self, message, phone_number=None):
        self._send_sms(str(self.phone_number if not phone_number else phone_number), message)

    def send_push(self, data, message):
        devices = self.devices.filter(is_active=True)
        for device in devices:
            send_unique_push.delay(
                device.os_id,
                {
                    "en": message,
                    # "ru": translate("ru", message)
                },
                data=data
            )

    def send_verify_email(self):

        email_address, created = EmailAddress.objects.get_or_create(
            user=self, email__iexact=self.email, defaults={"email": self.email}
        )
        confirmation = EmailConfirmation.create(email_address=email_address)
        confirmation.sent = timezone.now()
        confirmation.save()
        data = {
            self.email: {
                "key": confirmation.key,
                "name": self.name
            }
        }
        self.send_email(subject="Verify your email", to=[self.email],
                        template_name=constants.template_names.get("verify_email"), content={},
                        merge_vars=data)

    @property
    def email_verified(self):
        return self.emailaddress_set.filter(email=self.email, verified=True).exists()

    def generate_sms_code(self, commit=True):
        code = exrex.getone("[1-9]{4}")
        if settings.DEBUG:
            code = "1111"
        self.sms_code = code
        if commit:
            self.save()

    @property
    def rating_count(self):
        return self.seller_orders.filter(status="complete", rate__isnull=False).count()

    def recalculate_rating(self):
        rates = list(self.seller_orders.filter(status="complete", rate__isnull=False).values_list("rate", flat=True))
        rate = 0
        if rates:
            rate = sum(filter(lambda x: x, rates)) / len(rates)
            self.rating = round(rate, 2)
            self.save()
        return round(rate, 2)

    def refresh_auth_secret_key(self, commit=True):
        self.auth_secret_key = create_new_secret_key()
        if commit:
            self.save()


class Device(TimeStampedModel):
    user = models.ForeignKey(
        "users.User",
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="devices",
        null=True
    )
    os_id = models.CharField(
        _("One signal id"),
        max_length=150
    )
    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = _("User Device")
        verbose_name_plural = _("User Devices")

    def __str__(self):
        return f"{self.user.username} {self.os_id}"


class Profile(models.Model):

    EDUCATION_LEVEL_CHOICES = (
        (constants.EDUCATION_LEVEL_HIGH_SCHOOL_ENUM, constants.EDUCATION_LEVEL_HIGH_SCHOOL),
        (constants.EDUCATION_LEVEL_UNDERGRADUATE_ENUM, constants.EDUCATION_LEVEL_UNDERGRADUATE),
        (constants.EDUCATION_LEVEL_MASTERS_ENUM, constants.EDUCATION_LEVEL_MASTERS),
        (constants.EDUCATION_LEVEL_MBA_ENUM, constants.EDUCATION_LEVEL_MBA),
        (constants.EDUCATION_LEVEL_PHD_ENUM, constants.EDUCATION_LEVEL_PHD)
    )

    YEARS_OF_EXPERIENCE_CHOICES = (
        (constants.EXPERIENCE_ONE_TO_TWO_YEARS_ENUM, constants.EXPERIENCE_ONE_TO_TWO_YEARS),
        (constants.EXPERIENCE_THREE_TO_FIVE_YEARS_ENUM, constants.EXPERIENCE_THREE_TO_FIVE_YEARS),
        (constants.EXPERIENCE_SIX_TO_TEN_YEARS_ENUM, constants.EXPERIENCE_SIX_TO_TEN_YEARS),
        (constants.EXPERIENCE_ELEVEN_TO_FIFTEEN_YEARS_ENUM, constants.EXPERIENCE_ELEVEN_TO_FIFTEEN_YEARS),
        (constants.EXPERIENCE_SIXTEEN_TO_TWENTY_YEARS_ENUM, constants.EXPERIENCE_SIXTEEN_TO_TWENTY_YEARS),
        (constants.EXPERIENCE_TWENTY_ONE_TO_THIRTY_YEARS_ENUM, constants.EXPERIENCE_TWENTY_ONE_TO_THIRTY_YEARS),
        (constants.EXPERIENCE_THIRTY_PLUS_YEARS_ENUM, constants.EXPERIENCE_THIRTY_PLUS_YEARS)
    )

    COMPANY_TYPE_CHOICES = (
        (constants.COMPANY_TYPE_NOT_EMPLOYED_ENUM, constants.COMPANY_TYPE_NOT_EMPLOYED),
        (constants.COMPANY_TYPES_START_UP_ENUM, constants.COMPANY_TYPES_START_UP),
        (constants.COMPANY_TYPE_MNC_ENUM, constants.COMPANY_TYPE_MNC),
        (constants.COMPANY_TYPE_SME_ENUM, constants.COMPANY_TYPE_SME),
        (constants.COMPANY_TYPE_CONSULTANCY_ENUM, constants.COMPANY_TYPE_CONSULTANCY),
        (constants.COMPANY_TYPE_FUND_ENUM, constants.COMPANY_TYPE_FUND),
        (constants.COMPANY_TYPE_FREELANCE_ENUM, constants.COMPANY_TYPE_FREELANCE),
    )

    SECTOR_CHOICES = (
        (constants.SECTOR_TYPE_ADVISORY_CONSULTANCY_ENUM, constants.SECTOR_TYPE_ADVISORY_CONSULTANCY),
        (constants.SECTOR_TYPE_AGRICULTURE_ENUM, constants.SECTOR_TYPE_AGRICULTURE),
        (constants.SECTOR_TYPE_AI_ML_BLOCKCHAIN_ENUM, constants.SECTOR_TYPE_AI_ML_BLOCKCHAIN),
        (constants.SECTOR_TYPE_AIRLINE_AVIATION_ENUM, constants.SECTOR_TYPE_AIRLINE_AVIATION),
        (constants.SECTOR_TYPE_APPAREL_FASHION_ENUM, constants.SECTOR_TYPE_APPAREL_FASHION),
        (constants.SECTOR_TYPE_AUTOMOTIVE_TRANSPORTATION_ENUM, constants.SECTOR_TYPE_AUTOMOTIVE_TRANSPORTATION),
        (constants.SECTOR_TYPE_CIVIC_SOCIAL_ENUM, constants.SECTOR_TYPE_CIVIC_SOCIAL),
        (constants.SECTOR_TYPE_CONSUMER_SERVICES_ENUM, constants.SECTOR_TYPE_CONSUMER_SERVICES),
        (constants.SECTOR_TYPE_COSMETICS_ENUM, constants.SECTOR_TYPE_COSMETICS),
        (constants.SECTOR_TYPE_DESIGN_MEDIA_ENUM, constants.SECTOR_TYPE_DESIGN_MEDIA),
        (constants.SECTOR_TYPE_ECOMMERCE_ENUM, constants.SECTOR_TYPE_ECOMMERCE),
        (constants.SECTOR_TYPE_EDUCATION_ENUM, constants.SECTOR_TYPE_EDUCATION),
        (constants.SECTOR_TYPE_ENTERTAINMENT_ENUM, constants.SECTOR_TYPE_ENTERTAINMENT),
        (constants.SECTOR_TYPE_OFFLINE_ENUM, constants.SECTOR_TYPE_OFFLINE),
        (constants.SECTOR_TYPE_FINANCE_ENUM, constants.SECTOR_TYPE_FINANCE),
        (constants.SECTOR_TYPE_FOOD_BEVERAGE_ENUM, constants.SECTOR_TYPE_FOOD_BEVERAGE),
        (constants.SECTOR_TYPE_GAMING_ENUM, constants.SECTOR_TYPE_GAMING),
        (constants.SECTOR_TYPE_HEALTH_WELLNESS_ENUM, constants.SECTOR_TYPE_HEALTH_WELLNESS),
        (constants.SECTOR_TYPE_HOSPITALITY_ENUM, constants.SECTOR_TYPE_HOSPITALITY),
        (constants.SECTOR_TYPE_IT_ENUM, constants.SECTOR_TYPE_IT),
        (constants.SECTOR_TYPE_INVESTMENT_CAPITAL_ENUM, constants.SECTOR_TYPE_INVESTMENT_CAPITAL),
        (constants.SECTOR_TYPE_LEGAL_ENUM, constants.SECTOR_TYPE_LEGAL),
        (constants.SECTOR_TYPE_LEISURE_TRAVEL_TOURISM_ENUM, constants.SECTOR_TYPE_LEISURE_TRAVEL_TOURISM),
        (constants.SECTOR_TYPE_LUXURY_CONSUMER_GOODS_ENUM, constants.SECTOR_TYPE_LUXURY_CONSUMER_GOODS),
        (constants.SECTOR_TYPE_MARKETING_ADVERTING_ENUM, constants.SECTOR_TYPE_MARKETING_ADVERTING),
        (constants.SECTOR_TYPE_PACKAGING_DISTRIBUTION_ENUM, constants.SECTOR_TYPE_PACKAGING_DISTRIBUTION),
        (constants.SECTOR_TYPE_PHARMA_ENUM, constants.SECTOR_TYPE_PHARMA),
        (constants.SECTOR_TYPE_PHILANTHROPY_ENUM, constants.SECTOR_TYPE_PHILANTHROPY),
        (constants.SECTOR_TYPE_REAL_ESTATE_ENUM, constants.SECTOR_TYPE_REAL_ESTATE),
        (constants.SECTOR_TYPE_RENEWABLE_ENVIRONMENT_ENUM, constants.SECTOR_TYPE_RENEWABLE_ENVIRONMENT),
        (constants.SECTOR_TYPE_SPORTS_ENUM, constants.SECTOR_TYPE_SPORTS),
        (constants.SECTOR_TYPE_STAFFING_AND_RECRUITING_ENUM, constants.SECTOR_TYPE_STAFFING_AND_RECRUITING),
        (constants.SECTOR_TYPE_COMMUNITY_SOCIAL_ENUM, constants.SECTOR_TYPE_COMMUNITY_SOCIAL),
        (constants.SECTOR_TYPE_TECHNOLOGY_INTERNET_SOFTWARE_ENUM, constants.SECTOR_TYPE_TECHNOLOGY_INTERNET_SOFTWARE),
        (constants.SECTOR_TYPE_CIVIL_MECHANICAL_ELECTRICAL_ENUM, constants.SECTOR_TYPE_CIVIL_MECHANICAL_ELECTRICAL),
        (constants.SECTOR_TYPE_LOGISTICS_ENUM, constants.SECTOR_TYPE_LOGISTICS),
        (constants.SECTOR_TYPE_OTHER_ENUM, constants.SECTOR_TYPE_OTHER)
    )

    NUMBER_OF_EMPLOYEE_CHOICES = (
        (constants.NUMBER_OF_EMPLOYEE_UPTO_10_ENUM, constants.NUMBER_OF_EMPLOYEE_UPTO_10),
        (constants.NUMBER_OF_EMPLOYEE_UPTO_50_ENUM, constants.NUMBER_OF_EMPLOYEE_UPTO_50),
        (constants.NUMBER_OF_EMPLOYEE_UPTO_100_ENUM, constants.NUMBER_OF_EMPLOYEE_UPTO_100),
        (constants.NUMBER_OF_EMPLOYEE_UPTO_500_ENUM, constants.NUMBER_OF_EMPLOYEE_UPTO_500),
        (constants.NUMBER_OF_EMPLOYEE_500_PLUS_ENUM, constants.NUMBER_OF_EMPLOYEE_500_PLUS),
    )

    PROJECT_TYPE_CHOICES = (
        (constants.PROJECT_TYPE_MARKETING_ENUM, constants.PROJECT_TYPE_MARKETING),
        (constants.PROJECT_TYPE_GRAPHIC_DESIGN_ENUM, constants.PROJECT_TYPE_GRAPHIC_DESIGN),
        (constants.PROJECT_TYPE_VIDEOGRAPHY_ENUM, constants.PROJECT_TYPE_VIDEOGRAPHY),
        (constants.PROJECT_TYPE_UI_UX_ENUM, constants.PROJECT_TYPE_UI_UX),
        (constants.PROJECT_TYPE_SOFTWARE_DEV_ENUM, constants.PROJECT_TYPE_SOFTWARE_DEV),
    )

    STAGE_OF_COMPANY_CHOICES = (
        (constants.STAGE_OF_COMPANY_IDEA_STAGE_ENUM, constants.STAGE_OF_COMPANY_IDEA_STAGE),
        (constants.STAGE_OF_COMPANY_SEED_ENUM, constants.STAGE_OF_COMPANY_SEED),
        (constants.STAGE_OF_COMPANY_SERIES_A_ENUM, constants.STAGE_OF_COMPANY_SERIES_A),
        (constants.STAGE_OF_COMPANY_SERIES_B_ENUM, constants.STAGE_OF_COMPANY_SERIES_B),
        (constants.STAGE_OF_COMPANY_SERIES_C_ENUM, constants.STAGE_OF_COMPANY_SERIES_C),
        (constants.STAGE_OF_COMPANY_SERIES_D_PLUS_ENUM, constants.STAGE_OF_COMPANY_SERIES_D_PLUS),
    )

    COMPANIES_INVESTED_CHOICES = (
        (constants.COMPANY_INVESTED_NONE_ENUM, constants.COMPANY_INVESTED_NONE),
        (constants.COMPANY_INVESTED_1_TO_5_ENUM, constants.COMPANY_INVESTED_1_TO_5),
        (constants.COMPANY_INVESTED_5_TO_10_ENUM, constants.COMPANY_INVESTED_5_TO_10),
        (constants.COMPANY_INVESTED_10_TO_20_ENUM, constants.COMPANY_INVESTED_10_TO_20),
        (constants.COMPANY_INVESTED_20_PLUS_ENUM, constants.COMPANY_INVESTED_20_PLUS),
    )

    user = models.OneToOneField(
        "users.User",
        related_name="profile",
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Company Name"),
        null=True,
        blank=True
    )
    tag_line = models.CharField(
        verbose_name=_("Tag line"),
        max_length=100,
        blank=True,
        null=True
    )
    photo = models.ImageField(
        upload_to="profile/photo/%Y/%m/%d",
        verbose_name=_("Photo"),
        null=True,
        blank=True,
        validators=[SizeValidator(size=30)]
    )
    photo_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Photo Url"),
        max_length=1024
    )
    cover = models.ForeignKey(
        "users.CoverFile",
        null=True,
        blank=True,
        verbose_name=_("Cover File"),
        related_name="profiles",
        on_delete=models.SET_NULL
    )

    # TODO(Nishant): Make it text field and push.
    introduction = models.TextField(
        verbose_name=_("Introduction"),
        blank=True,
        null=True
    )
    focus = models.CharField(
        max_length=800,
        verbose_name=_("Focus"),
        blank=True,
        null=True
    )
    additional_information = models.CharField(
        max_length=800,
        verbose_name=_("Additional Information"),
        blank=True,
        null=True
    )
    linkedin_url = models.CharField(
        verbose_name=_("Linked In"),
        blank=True,
        null=True,
        max_length=800
    )

    # This is the url people want to showcase on their profile.
    primary_url = models.URLField(
        verbose_name=_("Showcase URL"),
        null=True,
        blank=True
    )
    instagram = models.CharField(
        verbose_name=_("Instagram"),
        null=True,
        blank=True,
        max_length=800
    )
    instagram_id = models.CharField(
        verbose_name=_("Instagram Id"),
        null=True,
        blank=True,
        max_length=32
    )
    instagram_username = models.CharField(
        blank=True,
        null=True,
        max_length=400,
        verbose_name=_("Instagram username")
    )
    twitter = models.CharField(
        verbose_name=_("Twitter"),
        blank=True,
        null=True,
        max_length=255
    )
    work_city = models.ForeignKey(
        "tags.WorkCityProxy",
        null=True,
        blank=True,
        verbose_name=_("Work city"),
        on_delete=models.CASCADE
    )
    tags = models.ManyToManyField(
        "tags.Tag",
        verbose_name=_("Tags"),
        related_name="profiles"
    )
    # TODO(Nishant): Remove the old tags once new_tag is filled for all users.
    new_tag = models.ManyToManyField(
        "tags.Tag",
        verbose_name=_("New Tag")
    )
    public_profile = models.BooleanField(
        default=True,
        verbose_name=_("Public Profile")
    )
    generated_introduction = models.TextField(
        max_length=1024,
        verbose_name=_("Auto Generated Introduction"),
        blank=True,
        null=True
    )
    opted_in_for_whatsapp = models.BooleanField(
        default=True,
        verbose_name=_("Whatsapp Messaging Enabled")
    )
    interests = models.ManyToManyField(
        "tags.Interests",
        verbose_name=_("Interests")
    )
    education_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=EDUCATION_LEVEL_CHOICES
    )
    years_of_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=YEARS_OF_EXPERIENCE_CHOICES
    )
    company_name = models.TextField(
        blank=True,
        null=True,
        max_length=255,
    )
    company_type = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=COMPANY_TYPE_CHOICES
    )
    company_type_advised = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=COMPANY_TYPE_CHOICES
    )
    sector = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=SECTOR_CHOICES
    )
    number_of_employees = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=NUMBER_OF_EMPLOYEE_CHOICES
    )
    project_type = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=PROJECT_TYPE_CHOICES
    )
    stage_of_company = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=STAGE_OF_COMPANY_CHOICES
    )
    aspiration = models.ForeignKey(
        "tags.Tag",
        on_delete=models.CASCADE,
        related_name="aspiration_tag",
        null=True,
        blank=True,
    )
    profile_intro_updated = models.BooleanField(
        default=False,
    )
    companies_invested = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=COMPANIES_INVESTED_CHOICES
    )
    other_tag = models.TextField(
        blank=True,
        null=True,
        max_length=255,
    )
    allow_meeting_request = models.BooleanField(
        default=False
    )

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profile")

    def __str__(self):
        return self.user.name if self.user.name else self.user.username

    @property
    def is_instagram_set(self):
        return bool(self.instagram)

    def get_introduction(self):
        return self.introduction if self.introduction else self.generated_introduction

    def get_photo_url(self):
        return self.photo.url if self.photo else self.photo_url


class ProfileExtraInfoMeta(models.Model):
    question = models.TextField(max_length=800)
    tag = models.ForeignKey(
        "tags.Tag",
        related_name="questions_meta",
        on_delete=models.CASCADE,
    )


class Referral(TimeStampedModel):
    """Set referral relations between users."""
    user = models.OneToOneField(
        "users.User",
        verbose_name=_("Referral"),
        on_delete=models.CASCADE
    )
    amount = models.CharField(
        _("Total referral subscription amount"),
        null=True,
        max_length=100,
    )
    is_paid = models.BooleanField(_("Is paid"), default=False)
    is_rewarded = models.BooleanField(_("Is rewarded"), default=False)

    class Meta:
        verbose_name = _("Referral")
        verbose_name_plural = _("Referrals")
        ordering = ["user__referer__name"]


class Admin(User):
    proxy = True

    class Meta:
        verbose_name = _("Admin")
        verbose_name_plural = _("Admins")


class CoverFile(TimeStampedModel):
    file = models.FileField(
        upload_to="profile/cover/%Y/%m/%d/",
        verbose_name=_("Cover"),
        null=True,
        validators=[SizeValidator(size=512)],
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="cover_files"
    )
    cover_thumbnail = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Cover thumbnail")
    )
    cover_transcoder = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Cover transcoder")
    )
    transcoder_job_id = models.CharField(
        max_length=255,
        verbose_name=_("Transcoder job id"),
        null=True,
        blank=True
    )
    transcoder_job_success = models.BooleanField(
        default=False
    )
    transcoder_uuid = models.UUIDField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.file.name if self.file else "-"


class BaseSource(base_models.BaseModel):
    name = models.CharField(max_length=32)
    score = models.PositiveIntegerField()

    def __str__(self):
        return "{} - {}".format(self.name, self.score)


class Source(base_models.BaseModel):
    """This is the possible sources for user to come onto the platform."""
    name = models.CharField(max_length=128)
    base_source = models.ForeignKey(
        BaseSource,
        related_name="sources",
        on_delete=models.CASCADE
    )
    link = models.URLField(max_length=128, null=True, blank=True)
    # This is a base score associated with the user.
    score = models.PositiveIntegerField(default=0)

    def __str__(self):
        return "{} - {}".format(self.name, self.score)


class UserActivity(base_models.BaseModel):
    """This model stores users last active time."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_active = models.DateTimeField()


@receiver(post_save, sender=CoverFile)
def profile_post_save(sender, instance, created,  *args, **kwargs):
    if created:
        transaction.on_commit(lambda: start_transcoding_for_cover_file.delay(instance.pk))


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created,  *args, **kwargs):
    if not (hasattr(instance, "notification_settings") and instance.notification_settings):
        UserNotificationsSettings.objects.create(user=instance)
    if created and not instance.subscriptions.filter(is_active=True):
        Subscription.objects.create(
            user=instance,
            date_start=timezone.now().date(),
            date_end=datetime.date(2020, 12, 1),
        )
