import base64
import logging
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_jwt.settings import api_settings

User = get_user_model()

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class UserTestCase(TestCase):
    email = "test@test.com"
    password = "testtest"
    credentials = {"email": email, "password": password}
    user_data = {"email": email, "password": password, "first_name": "First", "last_name": "Last"}
    client = APIClient()

    def setUp(self):
        logging.disable(logging.INFO)
        self.user = User.objects.create_superuser(**self.credentials)
        self.client = APIClient()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        super().tearDown()

    def authorize(self):
        payload = jwt_payload_handler(self.user)
        token = jwt_encode_handler(payload)
        self.client.credentials(HTTP_AUTHORIZATION=f"{api_settings.JWT_AUTH_HEADER_PREFIX} {token}")
        self.client.login(**self.credentials)
        return self.client

    def basic_auth(self):
        credentials = base64.b64encode(f'{self.email}:{self.password}'.encode("utf-8")).strip()
        auth_string = f'Basic {credentials.decode("utf-8")}'
        self.client.credentials(HTTP_AUTHORIZATION=auth_string)
        return self.client


class BaseTestCase(UserTestCase):

    def get(self, path: str, query_params: dict = None, *args, **kwargs):
        if query_params:
            path += f"?{urlencode(query_params)}"
        return self.authorize().get(path=path, *args, **kwargs)

    def post(self, path: str, data: dict = None, format: str = "json", *args, **kwargs):
        return self.authorize().post(path=path, data=data, format=format, *args, **kwargs)

    def put(self, path: str, data: dict = None, format: str = "json", *args, **kwargs):
        return self.authorize().put(path=path, data=data, format=format, *args, **kwargs)

    def patch(self, path: str, data: dict = None, format: str = "json", *args, **kwargs):
        return self.authorize().patch(path=path, data=data, format=format, *args, **kwargs)

    def delete(self, path: str, query_params: dict = None, *args, **kwargs):
        if query_params:
            path += f"?{urlencode(query_params)}"
        return self.authorize().delete(path=path, query_params=query_params, format=format, *args, **kwargs)
