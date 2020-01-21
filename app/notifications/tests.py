from django.contrib.auth import models as auth_models
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from users import models


class AuthTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(
            email='test@email.com',
            name='ftest ltest'
        )
        group = auth_models.Group.objects.get(name='User')
        self.user.groups.add(group)
        self.user.set_password('Qwer1234!')
        self.user.save()
        self.token = jwt_encode(self.user)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'settings': reverse('v1:notifications:user-settings-list')
        }

    def test_set_up_success(self):
        self.assertEqual(1, 1)

    def test_get_settings_fail_unauth(self):
        endpoint = self.endpoints.get('settings')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_get_settings_success(self):
        endpoint = self.endpoints.get('settings')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        for value in resp.json().values():
            self.assertTrue(value)

    def test_change_settings_success(self):
        endpoint = self.endpoints.get('settings')
        data = {
            'messages': False,
            'post_comments': False,
            'post_likes': False,
            'new_videos_posted': False,
            'new_articles_posted': False,
            'new_events_created': False,
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        get_resp = self.auth_client.get(endpoint, content_type='application/json')
        for value in get_resp.json().values():
            self.assertFalse(value)
