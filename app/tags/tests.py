from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from tags import models
from users import models as user_models


class CityTestCase(TestCase):
    def setUp(self):
        self.user = user_models.User.objects.create(
            email='test@email.com',
            name='ftest ltest'
        )
        self.user.set_password('Qwer1234!')
        self.user.save()
        self.token = jwt_encode(self.user)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'list': reverse('v1:tags:tag-list'),
            'detail': lambda x: reverse('v1:tags:tag-detail', kwargs={'pk': x})
        }
        self.tag = models.Tag.objects.create(name='Tag')

    def test_list_fail_unauth(self):
        endpoint = self.endpoints.get('list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_list_success(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(1, len(resp.json()))
        self.assertEqual('Tag', resp.json()[0]['name'])

    def test_retrieve_success(self):
        endpoint = self.endpoints.get('detail')(self.tag.pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual('Tag', resp.json()['name'])

    def test_retrieve_fail_unauth(self):
        endpoint = self.endpoints.get('detail')(self.tag.pk)
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)


