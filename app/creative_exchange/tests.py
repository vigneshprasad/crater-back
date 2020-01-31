from unittest import mock

import pytz
from django.core.files import File
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from creative_exchange import models
from locations.models import Country
from tags.models import CityProxy
from users import models as user_models
from utils.file_test_service import get_test_base64_image


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
        endpoint = self.endpoints.get('category-detail')(self.category.pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertIn('name', resp.json())


class ExchangeRequestTestCase(TestCase):

    def setUp(self):
        self.local_tz = pytz.timezone('Asia/Calcutta')
        self.dt_fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
        self.country = Country.objects.create(name='Test')
        self.city = CityProxy.objects.create(
            name='City',
            country=self.country
        )
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
            'request-list': reverse('v1:creative-exchange:request-list'),
            'request-detail': lambda x: reverse('v1:creative-exchange:request-detail', kwargs={'pk': x}),
            'quote-list': reverse('v1:creative-exchange:quote-list')
        }
        self.category = models.ExchangeCategory.objects.create(name='Category')
        self.category2 = models.ExchangeCategory.objects.create(name='Category', is_active=False)
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'
        self.requests = []
        for i in range(1, 26):
            request = models.ExchangeRequest.objects.create(
                category=self.category,
                user=self.user,
                title='Title',
                city=self.city,
                cover_image=file_mock,
                description='Description',
                special_requirement='Requirements',
                additional_information='Info',
                extended_price=i * 100
            )
            self.requests.append(request)

    def test_success_setup(self):
        self.assertEqual(1, 1)

    def test_get_list_fail_unauth(self):
        endpoint = self.endpoints.get('request-list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_list_success(self):
        endpoint = self.endpoints.get('request-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(20, len(resp.json()['results']))

    def test_get_list_success_with_page_size(self):
        endpoint = self.endpoints.get('request-list')
        resp = self.auth_client.get(f'{endpoint}?page_size=10', content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(10, len(resp.json()['results']))

    def test_get_list_success_data(self):
        endpoint = self.endpoints.get('request-list')
        resp = self.auth_client.get(f'{endpoint}?page_size=10', content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(10, len(resp.json()['results']))
        d = resp.json()['results'][0]
        request = self.requests[24]
        cover_image = d.pop('cover_image')
        self.assertTrue(cover_image)
        data = {
            'pk': request.pk,
            'title': request.title,
            'extended_price': request.extended_price,
            'city': self.city.pk,
            'city_name': self.city.name,
            'created': request.created.replace(tzinfo=pytz.utc).astimezone(self.local_tz).strftime(self.dt_fmt),
            'user_name': self.user.name,
            'user_logo': None,
            'category': request.category.pk,
            'category_name': request.category.name,
            'days': request.days,
            'require': request.require,
            'description': request.description,
            'special_requirement': request.special_requirement,
            'additional_information': request.additional_information,
            'files_urls': [],
            'quotes_count': 0
        }
        self.assertDictEqual(d, data)

    def test_get_retrieve_success(self):
        endpoint = self.endpoints.get('request-detail')(self.requests[0].pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        d = resp.json()
        request = self.requests[0]
        cover_image = d.pop('cover_image')
        self.assertTrue(cover_image)
        historcial_bids = d.pop('historical_bids')
        graph_data = d.pop('graph_data')
        self.assertFalse(historcial_bids)
        self.assertFalse(graph_data['half_year_avf'])
        self.assertEqual(180, len(graph_data['data'].values()))
        data = {
            'pk': request.pk,
            'title': request.title,
            'extended_price': request.extended_price,
            'city': self.city.pk,
            'city_name': self.city.name,
            'created': request.created.replace(tzinfo=pytz.utc).astimezone(self.local_tz).strftime(self.dt_fmt),
            'user_name': self.user.name,
            'user_logo': None,
            'category': request.category.pk,
            'category_name': request.category.name,
            'days': request.days,
            'require': request.require,
            'description': request.description,
            'special_requirement': request.special_requirement,
            'additional_information': request.additional_information,
            'files_urls': [],
            'quotes_count': 0
        }
        self.assertDictEqual(d, data)

    def test_post_success(self):
        endpoint = self.endpoints.get('request-list')
        data = {
            'category': self.category.pk,
            'title': 'string',
            'city': self.city.pk,
            'days': 1,
            'require': True,
            'description': 'string',
            'special_requirement': 'string',
            'additional_information': 'string',
            'extended_price': 100,
            'cover_image_base64': get_test_base64_image(),
            'files_base64': [get_test_base64_image(), get_test_base64_image()]
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(201, resp.status_code)
        self.assertEqual(len(resp.json()['files_urls']), 2)
        self.assertTrue(resp.json()['cover_image'])

    def test_post_quote_for_request(self):
        endpoint = self.endpoints.get('quote-list')
        data = {
            'exchange_request': self.requests[0].pk,
            'price': 100,
            'timeline': 20,
            'revisions': 5,
            'year_of_experience': 10,
            'followers': 100,
            'includes': "Text",
            'additional_text': 'text',
            'require': 'text',
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(201, resp.status_code)
