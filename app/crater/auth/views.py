from django.contrib.auth.models import Group
from rest_auth.utils import jwt_encode

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from crater.auth import constants
from crater.auth import exceptions
from crater.auth import models
from crater.auth import serializers
from crater.auth import tasks
from users import constants as user_constants
from users import public as user_public
from users import permissions as user_permissions
from users import serializers as user_serializers
from users import utils as user_utils


class PhoneNumberRegisterView(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [user_permissions.AllowAny]
    serializer_class = serializers.PhoneOtpSerializer

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[user_permissions.AllowAny],
        serializer_class=serializers.PhoneOtpSerializer
    )
    def otp(self, request):
        request_data = request.data

        # We have to make sure the phone numbers are E64 compliant.
        username = request_data.get("username")

        if not username:
            no_username_provided_exception = exceptions.NoUsernameProvided()

            return Response(
                no_username_provided_exception.get_error_body(),
                status=no_username_provided_exception.status_code
            )

        # Validate serializer.
        data = {"username": username}

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        phone_otp = serializer.save()

        # Send the OTP sms to the user.
        user_utils.send_sms(
            phone_number=username,
            message=constants.LOGIN_OTP_MESSAGE.format(otp=phone_otp.otp)
        )

        return Response(
            {"message": "OTP sent to: {username}".format(username=username)},
            status=status.HTTP_200_OK
        )

    @action(
        methods=["post"],
        detail=False,
        serializer_class=serializers.PhoneOtpSerializer
    )
    def verify(self, request):
        """Verifies user's phone number based on the OTP provided.

        Note:
            The OTP is sent when the user is trying to log in to
            the app. Return user details to client.
        """
        request_data = request.data
        username = request_data.get("username")
        otp = request_data.get("otp")

        phone_otp = models.PhoneOtp.objects.filter(
            phone_number=username,
            otp=otp
        ).first()

        # Throw an error
        if not phone_otp:
            login_otp_mismatch_exception = exceptions.LoginOtpMismatch()
            return Response(
                login_otp_mismatch_exception.get_error_body(),
                status=login_otp_mismatch_exception.status_code
            )

        data = {"otp": otp}
        serializer = self.get_serializer(data=data, instance=phone_otp, partial=True)
        serializer.is_valid(raise_exception=True)

        user, created = user_public.get_or_create_user(phone_number=username)
        serializer.save(user=user)

        # Create a JWT token for the user for upcoming requests.
        token = jwt_encode(user)
        # Add user to crater club group.
        crater_club_group, _ = Group.objects.get_or_create(
            name=user_constants.CRATER_CLUB_GROUP
        )

        if crater_club_group not in user.groups.all():
            user.groups.add(crater_club_group)

            # Send welcome crater whatsapp after 2 minutes
            # on first login/signup on Crater.
            tasks.send_welcome_crater_whatsapp.apply_async(
                args=(user, ),
                countdown=60
            )

        # Getting user detail once the user is verified.
        user_details = user_serializers.UserDetailSerializer(user).data

        return Response(
            {"token": token, "user": user_details},
            status=status.HTTP_200_OK
        )
