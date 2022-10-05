from drf_spectacular.extensions import OpenApiAuthenticationExtension

from users.authentication import JSONWebTokenAuthentication


class JSONWebTokenAuthenticationScheme(OpenApiAuthenticationExtension):

    target_class = JSONWebTokenAuthentication
    name = "SwaggerAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
        }
