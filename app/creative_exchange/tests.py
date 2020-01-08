from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from creative_exchange import models
from users import models as user_models


class ExchangeCategoryTestCase(TestCase):
    def setUp(self):
        self.user = user_models.User.objects.create(
            email='test1@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user.set_password('Qwer1234!')
        self.user.save()
        self.token = jwt_encode(self.user)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'category-list': reverse('v1:creative-exchange:category-list'),
            'category-detail': lambda x: reverse('v1:creative-exchange:category-detail', kwargs={'pk': x})
        }
        self.category = models.ExchangeCategory.objects.create(name='Category')
        self.category2 = models.ExchangeCategory.objects.create(name='Category', is_active=False)

    def test_success_setup(self):
        self.assertEqual(1, 1)

    def test_get_list_fail_unauth(self):
        endpoint = self.endpoints.get('category-list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_list_success(self):
        endpoint = self.endpoints.get('category-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()))

    def test_get_retrieve_success(self):
        endpoint = self.endpoints.get('category-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()))
