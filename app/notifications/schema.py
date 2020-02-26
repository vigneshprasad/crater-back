from drf_yasg import openapi


batch_notification_read = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "type": openapi.Schema(type=openapi.TYPE_STRING, description='Notification type'),
    }
)
