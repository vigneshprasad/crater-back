import datetime

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import views as auth_views, get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_auth.registration.views import VerifyEmailView as DefaultVerifyEmailView
from rest_auth.utils import jwt_encode
from rest_auth.views import PasswordResetConfirmView as DefaultPasswordResetConfirmView, \
    UserDetailsView as DefaultUserDetailsView, LogoutView as RestLogoutView
from rest_framework import filters, mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from conversations import models as conversation_models
from conversations import private as conversation_private
from payment import models as payment_models, serializers as payment_serializers
from payment.tasks import charge_subscription_payment
from resources.meetings import models as meeting_models
from users import permissions, services, utils, signals, exceptions
from utils import messages
from utils.stripe_service import stripe_service
from . import serializers, models, constants
from .forms import AdminSetPasswordForm
from .models import Profile
from .paginators import Pagination
from .signals import basic_profile_created, phone_number_verified, referred_friend, profile_requested
from .swagger_schemas import referer_email
from .tasks import send_email


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    post_reset_login = True
    form_class = AdminSetPasswordForm
    success_url = reverse_lazy("admin:dashboard_dashboard_changelist")


class UserViewSet(
    viewsets.GenericViewSet
):
    serializer_class = serializers.UserDetailSerializer
    queryset = models.User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    )
    def count(self, request):
        count = self.get_queryset().count()
        return Response({
            "count": count + constants.BASE_USER_COUNT
        }, status=status.HTTP_200_OK)


class ProfileViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.ProfileSerializer
    queryset = models.Profile.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _update_data_for_user(user, user_data):
        """Update name for a user send in profile post.

        Args:
            user(User): Request user, who's profile is being updated.
            user_data(dict): User data being updated, through profile post.

        """
        if not user_data:
            return

        name = user_data.get("name")
        if not name:
            return

        user.set_name(name)

    def create(self, request, *args, **kwargs):
        """Create or update profile for a user."""
        user = request.user
        created_flag = True

        if user.has_profile:
            serializer = self.get_serializer(data=request.data, instance=request.user.profile, partial=True)
            created_flag = False
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        # TODO(Nishant): Fix and create and update endpoint as well.
        # Because of the user addition to validated data, anything with
        # source user.{} can't be updated through profile.

        # Update data for user.
        user_data = serializer.validated_data.get("user")
        self._update_data_for_user(user, user_data)

        # Perform create.
        serializer.validated_data["user"] = user
        self.perform_create(serializer)

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
        if hasattr(self.request.user, "profile") and self.request.user.profile:
            return self.request.user.profile
        return None

    def retrieve(self, request, *args, **kwargs):

        instance = self.get_object()

        if not instance:
            raise NotFound()

        photo = instance.photo if instance.photo else instance.photo_url
        serializer = self.get_serializer(instance)
        data = serializer.data
        data["photo"] = photo.url if hasattr(photo, "url") else photo

        # Everytime profile retrieve gets called we update user activity.
        profile_requested.send(
            sender=instance.__class__,
            profile=instance
        )

        return Response(data)


    def list(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @action(
        methods=["get"],
        detail=True,
        pagination_class=Pagination
    )
    def connections(self, request, pk, *args, **kwargs):
        """Return connections for the user on the platform."""
        try:
            user = models.User.objects.get(pk=pk)
        except (models.User.DoesNotExist, ValidationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        connections = []
        for meeting in meeting_models.Meeting.objects.filter(participants=user):
            for participant in meeting.participants.all().exclude(pk=user.pk):
                connections.append(participant)
        for group in conversation_models.Group.objects.filter(speakers=user):
            for speaker in group.speakers.all().exclude(pk=user.pk):
                connections.append(speaker)

        unique_connections = list(set(connections))

        # Need only connections with profile.
        unique_connections_with_profile = []
        for user in unique_connections:
            if not user.has_profile:
                continue
            unique_connections_with_profile.append(user.profile)

        # Sorting the users by score.
        unique_connections_with_profile.sort(key=lambda x: x.user.score, reverse=True)
        serialized = self.get_serializer(unique_connections_with_profile, many=True)

        return Response(serialized.data)


class BankDetailViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = payment_serializers.BankDetailsSerializer
    queryset = payment_models.BankDetails.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if hasattr(request.user, "bank_details") and request.user.bank_details:
            serializer = self.get_serializer(data=request.data, instance=request.user.bank_details, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["user"] = request.user
        stripe_token = serializer.validated_data.pop("stripe_token", None)
        if stripe_token:
            try:
                self.get_stripe_customer_id(serializer, stripe_token)
            except:
                raise serializers.serializers.ValidationError(
                    {"stripe_token": _("Stripe token is not valid")}
                )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(payment_serializers.BankDetailsSerializer(request.user.bank_details).data)

    def get_object(self):
        if hasattr(self.request.user, "bank_details") and self.request.user.bank_details:
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
        if serializer.instance and serializer.instance.stripe_customer_id:
            stripe_service.update_customer_source(
                serializer.instance.stripe_customer_id,
                stripe_token
            )
        else:
            serializer.validated_data["stripe_customer_id"] = stripe_service.get_customer_id(
                serializer.validated_data["user"],
                stripe_token
            )
        return serializer

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.stripe_customer_id:
            instance.card_data = stripe_service.get_customer_card_data(instance.stripe_customer_id)
        instance.save()
        if not instance.user.has_active_subscription and instance.membership_aggreed:
            charge_subscription_payment.delay(instance.user.pk)


class LogoutView(RestLogoutView):
    serializer_class = serializers.LogoutSerializer

    def logout(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        os_id = serializer.validated_data.get("os_id", "")

        # Send user logout signal.
        signals.user_logout.send(
            sender=self.__class__,
            user=user,
            os_id=os_id,
        )
        return super().logout(request)


class VerificationView(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.NewPhoneNumberSerializer

    @action(methods=["post"], detail=False, serializer_class=serializers.NewPhoneNumberSerializer)
    def new_phone_number(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        if phone_number:
            request.user.new_phone_number = phone_number
            request.user.generate_sms_code(commit=False)
            request.user.save()
            request.user._send_sms(
                phone_number,
                messages.PHONE_CODE_VERIFICATION.format(code=request.user.sms_code)
            )
        return Response({"status": messages.PHONE_CODE_SUCCESSFULLY_SENT})

    @action(methods=["post"], detail=False, serializer_class=serializers.CheckCodeSerializer)
    def check_sms_code(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.sms_code = ""
        if request.user.new_phone_number:
            request.user.phone_number = request.user.new_phone_number
            request.user.new_phone_number = ""
            phone_number_verified.send(
                sender=self.__class__,
                user=request.user,
                request=request
            )

        request.user.set_phone_number_verified()

        return Response({"status": messages.PHONE_NUMBER_SUCCESSFULLY_VERIFIED})

    @action(methods=["post"], detail=False)
    def send_verify_email(self, request):
        request.user.send_verify_email()
        return Response({"status": messages.EMAIL_VERIFY_SUCCESSFULLY_SENT})


class NetworkView(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericAPIView
):
    serializer_class = serializers.ProfileSerializer
    pagination_class = Pagination
    queryset = models.Profile.objects.select_related("user").all().order_by("name")
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ["new_tag"]
    search_fields = ["name"]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        photo = instance.photo
        if not photo:
            photo = instance.photo_url

        if instance:
            serializer = self.get_serializer(instance)
            data = serializer.data
            data["photo"] = photo.url if hasattr(photo, "url") else photo
            return Response(data)
        raise NotFound()

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if pk:
            try:
                self.kwargs["pk"] = get_user_model().objects.get(pk=pk).profile.pk
                return self.retrieve(request, *args, **kwargs)
            except (get_user_model().DoesNotExist, ValidationError, Profile.DoesNotExist):
                raise NotFound()
        return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """Returns list of users with 3+ meeting on the platform."""
        ids = services.get_user_with_number_of_meetings(
            number_of_meeting=3
        )

        queryset = self.filter_queryset(
            self.get_queryset()
        )

        # Keeping people with photo's up in the list of users.
        results = queryset.filter(user__pk__in=ids).order_by("-photo")
        page = self.paginate_queryset(results)

        if page is None:
            serialized = self.get_serializer(results, many=True)
            return Response(serialized.data)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class RefererEmailView(APIView):

    @swagger_auto_schema(request_body=referer_email)
    def post(self, request):
        uuid = str(request.user.pk)
        fernet = Fernet(settings.FERNET_KEY)
        encrypted_uuid = fernet.encrypt(uuid.encode("ascii"))
        try:
            email = request.data.get("email").strip()
            validate_email(email)
            if get_user_model().objects.filter(email=email).exists():
                return Response({"email": _("Email already exists.")}, status=status.HTTP_400_BAD_REQUEST)
            data = {
                email: {
                    "key": encrypted_uuid.decode("ascii"),
                    "user": str(request.user),
                    "front_url": settings.FRONT_URL
                }
            }
            send_email.delay(
                subject=_("Signup invitation"),
                to=[email],
                template_name=constants.template_names.get("invite_friend"),
                content={},
                merge_vars=data)
            referred_friend.send(
                sender=self.__class__,
                user=request.user,
                request=request
            )
            return Response({"detail": _("Verification e-mail sent."), "email": email})
        except (ValidationError, AttributeError):
            return Response({"email": _("Email is not valid.")}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(DefaultVerifyEmailView):

    def get_serializer(self, *args, **kwargs):
        return serializers.VerifyEmailSerializer(*args, **kwargs)


class CoverFileViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = models.CoverFile.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CoverFileSerializer

    def perform_create(self, serializer):
        serializer.validated_data["user"] = self.request.user
        serializer.save()


class UserDetailsView(DefaultUserDetailsView):

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        user = request.user
        # Send the new JWT token on user update.
        return Response(
            {
                "token": jwt_encode(user),
                "user": response.data
            },
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmAPIView(DefaultPasswordResetConfirmView):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        data = serializer.data
        uid = force_text(urlsafe_base64_decode(data["uid"]))
        try:
            user = models.User.objects.get(pk=uid)
        except models.User.DoesNotExist:
            return
        # Marking email as verified if not already verified.
        utils.mark_email_as_verified(user)

        return super().post(request, *args, **kwargs)


class ProfileMetaViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(
        methods=["GET"],
        detail=True,
    )
    def tag_extra_info(self, request, pk, *args, **kwargs):
        try:
            meta_object = models.ProfileExtraInfoMeta.objects.get(tag=pk)
            serialized = serializers.ProfileExtraInfoMetaSerializer(meta_object)

            return Response(serialized.data)
        except models.ProfileExtraInfoMeta.DoesNotExist:
            return Response("Missing object", status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["GET"],
        detail=False
    )
    def education(self, request, *args, **kwargs):
        data = []
        for item in models.Profile.EDUCATION_LEVEL_CHOICES:
            data.append({
                "value": item[0],
                "name": item[1],
            })

        return Response(data)

    @action(
        methods=["GET"],
        detail=False
    )
    def experience(self, request, *args, **kwargs):
        data = []
        for item in models.Profile.YEARS_OF_EXPERIENCE_CHOICES:
            data.append({
                "value": item[0],
                "name": item[1],
            })

        return Response(data)

    @action(
        methods=["GET"],
        detail=False
    )
    def company(self, request, *args, **kwargs):
        data = []
        for item in models.Profile.COMPANY_TYPE_CHOICES:
            data.append({
                "value": item[0],
                "name": item[1],
            })

        return Response(data)

    @action(
        methods=["GET"],
        detail=False
    )
    def sector(self, request, *args, **kwargs):
        data = []
        for item in models.Profile.SECTOR_CHOICES:
            data.append({
                "value": item[0],
                "name": item[1],
            })

        return Response(data)


class UserReferralViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = models.UserReferral.objects.exclude(
        status=constants.REFERRAL_STATUS_PAYMENT_CANCELLED_ENUM
    ).select_related(
        "stream",
        "stream__topic"
    ).order_by(
        "-created_at"
    )
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.UserReferralSerializer
    pagination_class = Pagination

    def list(self, request, *args, **kwargs):
        user = request.user
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                referrer__pk=user.pk
            )
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        methods=["GET"],
        detail=False,
    )
    def summary(self, request):
        user = request.user
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                referrer__pk=user.pk
            ).exclude(
                status=constants.REFERRAL_STATUS_USER_ACTION_PENDING_ENUM
            )
        )

        referrals_summary = services.get_referrals_summary(
            user_referrals=queryset
        )

        return Response(referrals_summary)


class UserPermissionViewSet(viewsets.GenericViewSet):

    serializer_class = serializers.UserPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.UserPermission.objects.all()

    def list(self, request, *args, **kwargs):
        user = request.user
        try:
            obj = self.get_queryset().get(user=user)
        except models.UserPermission.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = self.get_serializer(obj).data
        return Response(data, status=status.HTTP_200_OK)


class UserCategoryViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = serializers.UserCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.UserCategory.objects.all()

    @action(
        methods=["POST"],
        detail=False,
    )
    def follow(self, request):
        user = request.user
        data = request.data

        # Category validation
        category = conversation_private.get_category_by_slug(
           slug=data.get("category")
        )
        if not category:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user_category = services.get_user_category(
            user=user,
            category=category
        )
        if user_category and user_category.followed:
            category_already_followed_exception = exceptions.CategoryAlreadyFollowed()
            return Response(
                category_already_followed_exception.get_error_body(),
                status=category_already_followed_exception.status_code
            )

        data = {
            "user": user.pk,
            "category": category.id,
            "followed": True,
            "followed_at": datetime.datetime.now()
        }

        if user_category:
            serializer = self.get_serializer(data=data, instance=user_category, partial=True)
        else:
            serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=["POST"],
        detail=False,
    )
    def unfollow(self, request):
        user = request.user
        data = request.data

        # Category validation
        category = conversation_private.get_category_by_slug(
            slug=data.get("category")
        )
        if not category:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user_category = services.get_user_category(
            user=user,
            category=category
        )
        if not user_category:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not user_category.followed:
            category_already_unfollowed_exception = exceptions.CategoryAlreadyUnfollowed()
            return Response(
                category_already_unfollowed_exception.get_error_body(),
                status=category_already_unfollowed_exception.status_code
            )

        data = {
            "user": user.pk,
            "category": category.id,
            "followed": False,
            "unfollowed_at": datetime.datetime.now()
        }
        serializer = self.get_serializer(data=data, instance=user_category, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
