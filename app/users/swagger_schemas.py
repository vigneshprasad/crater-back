from drf_yasg import openapi


referer_email = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "email": openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
    }
)
