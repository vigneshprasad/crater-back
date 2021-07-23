from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from devices import signals as device_signals
from users import permissions
from wn_analytics import constants


class SegmentWebhookViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.SegmentRequest]

    @staticmethod
    def generate_bad_request(data):
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["post"],
        detail=False,
    )
    def identify(self, request):
        """Catches webhooks for segment identify calls."""
        request_data = request.data
        if not request_data.get("type") == constants.SEGMENT_IDENTIFY:
            return Response(status=status.HTTP_200_OK)

        context = request_data.get("context", {})
        email = request_data.get("traits").get("email")
        # If the request has no email, throw an error.
        if not email:
            return self.generate_bad_request(
                {"error": "No Email Found"}
            )

        # Get the user.
        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            return self.generate_bad_request(
                {"error": "Invalid Email"}
            )

        # If not device data is present throw and error.
        device_data = context.get("device", None)
        if not device_data:
            return self.generate_bad_request(
                {"error": "Device Data Not Found"}
            )

        device_manufacturer = device_data.get("manufacture")
        device_model = device_data.get("model")
        device_type = device_data.get("type")

        if device_type == constants.DEVICE_TYPE_IOS:
            if not device_manufacturer:
                device_manufacturer = constants.DEFAULT_IOS_DEVICE_MANUFACTURER
            if not device_model:
                device_model = constants.DEFAULT_IOS_DEVICE_MODEL

        # Create user device for the user.
        device_signals.new_user_device_detected.send(
            sender=user.__class__,
            user=user,
            device_name=device_manufacturer,
            device_model=device_model,
            device_price=None
        )

        return Response(status=status.HTTP_200_OK)
