from unittest import mock

from django.core.files import File
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from services import models
from users import models as user_models


class CategoryTestCase(TestCase):
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
            'list': reverse('v1:services:category-list'),
            'detail': lambda x: reverse('v1:services:category-detail', kwargs={'pk': x})
        }
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'
        self.category = models.ProfessionalCategoryProxy.objects.create(name='Category')
        self.category2 = models.ProfessionalCategoryProxy.objects.create(name='Category2', photo=file_mock)
        self.marketing = models.MarketingCategoryProxy.objects.create(name='Category3')
        self.service_type = models.ServiceType.objects.create(
            name='Type', category=self.category, description='Description', group='service'
        )

    def test_list_fail_unauth(self):
        endpoint = self.endpoints.get('list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_list_success(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(3, len(resp.json()))
        self.assertEqual('Category', resp.json()[0]['name'])
        self.assertEqual(1, len(resp.json()[0]['service_types']))

    def test_retrieve_success(self):
        endpoint = self.endpoints.get('detail')(self.category.pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual('Category', resp.json()['name'])
        self.assertIsNone(resp.json()['photo'])

    def test_retrieve_fail_unauth(self):
        endpoint = self.endpoints.get('detail')(self.category.pk)
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_retrieve_success_photo(self):
        endpoint = self.endpoints.get('detail')(self.category2.pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual('Category2', resp.json()['name'])
        self.assertTrue(resp.json()['photo'])

    def test_list_professional(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?direction=professional', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(2, len(resp.json()))

    def test_list_marketing(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?direction=marketing', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(1, len(resp.json()))


