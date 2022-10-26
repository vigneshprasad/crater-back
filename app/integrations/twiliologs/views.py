import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from integrations.twiliologs import models
from users import permissions as user_permissions


class TwilioSMSViewSet(GenericViewSet):

    permission_classes = [user_permissions.AllowAny]

    @action(
        methods=["POST"],
        detail=False
    )
    def status(self, request):
        """Webhook for status update on messages sent by
            Twilio.

        """
        data = request.data
        message_sid = data.get("MessageSid")
        message_status = data.get("MessageStatus")

        try:
            sms = models.SMS.objects.get(sid=message_sid)
        except models.SMS.DoesNotExist:
            logging.error("SMSLog does not exist for SID: {}".format(message_sid))
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        # Update the status of the message status.
        sms.status = message_status
        sms.save()

        return Response(status=status.HTTP_200_OK)
