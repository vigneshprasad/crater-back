from unittest import mock

from django.core.files import File
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from payment.models import BankDetails
from services import models
from tags.models import Industry
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


class ServiceTestCase(TestCase):
    def setUp(self):
        self.user = user_models.User.objects.create(
            email='test@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user2 = user_models.User.objects.create(
            email='test1@email.com',
            name='ftest ltest',
            is_approved=True
        )
        BankDetails.objects.create(
            user=self.user,
            membership='premium'
        )
        BankDetails.objects.create(
            user=self.user2,
            membership='premium'
        )
        self.user.set_password('Qwer1234!')
        self.user.save()
        self.token = jwt_encode(self.user)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'list': reverse('v1:services:user-service-list'),
            'detail': lambda x: reverse('v1:services:user-service-detail', kwargs={'pk': x})
        }
        self.category = models.ProfessionalCategoryProxy.objects.create(name='Category')
        self.category2 = models.ProfessionalCategoryProxy.objects.create(name='Category2')
        self.service_type = models.ServiceType.objects.create(
            name='Type', category=self.category, description='Description', group='service'
        )
        self.service_type2 = models.ServiceType.objects.create(
            name='Type2', category=self.category2, description='Description', group='call_request'
        )
        self.industry1 = Industry.objects.create(name='Industry')
        self.industry2 = Industry.objects.create(name='Industry2')
        self.user_service_info = models.UserServiceInfo.objects.create(
            user=self.user,
            professional_service_provider=True,
            generate_business=True,
        )
        self.user_service_info2 = models.UserServiceInfo.objects.create(
            user=self.user2,
            professional_service_provider=True,
            generate_business=True,
        )
        self.user_service_info.industries.add(self.industry1)
        self.user_service_info2.industries.add(self.industry2)
        for i in range(1, 26):
            s1 = models.Service.objects.create(
                service_type=self.service_type,
                user=self.user,
                status='approved' if 5 < i < 21 else 'unknown',
                price_type='price',
                price=i*200,
                rating=i*0.1,
                timeline=60,
                attachments=[],
                questions=[]
            )
            self.user_service_info.services.add(s1)
            s2 = models.Service.objects.create(
                service_type=self.service_type2,
                user=self.user2,
                status='approved' if 5 < i < 21 else 'unknown',
                price_type='price',
                price=i * 200,
                rating=i * 0.1,
                timeline=60,
                attachments=[],
                questions=[]
            )
            self.user_service_info2.services.add(s2)

    def test_list_fail_unauth(self):
        endpoint = self.endpoints.get('list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_list_success(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(20, len(resp.json()['results']))

    def test_list_success_paginated(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?page_size=10', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_price_to_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?price_to=2000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_price_from_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?price_from=3000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(12, len(resp.json()['results']))

    def test_list_price_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?price_from=2000&price_to=3000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(12, len(resp.json()['results']))

    def test_list_rating_to_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?rating_to=1.0', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_rating_from_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?rating_from=1.5', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(12, len(resp.json()['results']))

    def test_list_rating_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?rating_from=1.0&rating_to=1.6', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(14, len(resp.json()['results']))

    def test_list_industries_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?user_infos__industries={self.industry1.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(15, len(resp.json()['results']))

    def test_list_industries_filter_2(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?user_infos__industries={self.industry1.pk}&user_infos__industries={self.industry2.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(20, len(resp.json()['results']))

    def test_list_category_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?service_type__category={self.category.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(15, len(resp.json()['results']))

    def test_list_category_filter_2(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?service_type__category={self.category2.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(15, len(resp.json()['results']))

    def test_list_service_type_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?service_type__group=service', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(15, len(resp.json()['results']))

    def test_list_service_type_filter_2(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?service_type__group=call_request', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(15, len(resp.json()['results']))

    def test_list_rating_ordering(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?ordering=-rating', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['results'][0]['rating'] >= resp.json()['results'][1]['rating'])
        self.assertTrue(resp.json()['results'][0]['rating'] >= resp.json()['results'][19]['rating'])

    def test_list_price_ordering(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?ordering=price', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['results'][0]['price'] <= resp.json()['results'][1]['price'])
        self.assertTrue(resp.json()['results'][0]['price'] <= resp.json()['results'][19]['price'])

    def test_list_desc_price_ordering(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?ordering=-price', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['results'][0]['price'] >= resp.json()['results'][1]['price'])
        self.assertTrue(resp.json()['results'][0]['price'] >= resp.json()['results'][19]['price'])
