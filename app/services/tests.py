from unittest import mock

from django.contrib.auth import models as auth_models
from django.core.files import File
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from locations.models import Country
from payment.models import BankDetails
from services import models
from tags.models import Industry, WorkCityProxy
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


class ProfessionalTestCase(TestCase):
    def setUp(self):
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
        self.country = Country.objects.create(name='Country')
        self.work_city = WorkCityProxy.objects.create(
            name='WorkCity1',
            country=self.country
        )
        self.work_city2 = WorkCityProxy.objects.create(
            name='WorkCity2',
            country=self.country
        )
        for i in range(1,21):
            user = user_models.User.objects.create(
                email=f'test{i}@email.com',
                name='ftest ltest',
                is_approved=True
            )
            BankDetails.objects.create(
                user=user,
                membership='premium'
            )
            user_service_info = models.UserServiceInfo.objects.create(
                user=user,
                professional_service_provider=True,
                generate_business=True,
                followers=i * 1000
            )
            if i > 10:
                user_models.Profile.objects.create(
                    user=user,
                    name='Profile',
                    work_city=self.work_city2
                )
                user_service_info.industries.add(self.industry1)
                s1 = models.Service.objects.create(
                    service_type=self.service_type,
                    user=user,
                    status='approved',
                    price_type='price',
                    price=i * 200,
                    rating=i * 0.1,
                    timeline=60,
                    attachments=[],
                    questions=[]
                )
            else:
                user_models.Profile.objects.create(
                    user=user,
                    name='Profile',
                    work_city=self.work_city
                )
                s1 = models.Service.objects.create(
                    service_type=self.service_type2,
                    user=user,
                    status='approved',
                    price_type='price',
                    price=i * 200,
                    rating=i * 0.1,
                    timeline=60,
                    attachments=[],
                    questions=[]
                )
                user_service_info.industries.add(self.industry2)
            user_service_info.services.add(s1)
        self.user = user_models.User.objects.create(
            email='test@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user.set_password('Qwer1234!')
        self.user.save()
        self.token = jwt_encode(self.user)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'list': reverse('v1:services:professionals-list'),
            'detail': lambda x: reverse('v1:services:professionals-detail', kwargs={'pk': x})
        }

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

    def test_list_success_category_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?category={self.category.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_success_city_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?city={self.work_city.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_success_category_city_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?city={self.work_city.pk}&category={self.category.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(0, len(resp.json()['results']))

    def test_list_price_to_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?price_to=2000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_price_from_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?price_from=2000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(11, len(resp.json()['results']))

    def test_list_price_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?price_from=2000&price_to=3000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(6, len(resp.json()['results']))

    def test_list_industries_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?user_services_info__industries={self.industry1.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_industries_filter_2(self):
        endpoint = self.endpoints.get('list')

        resp = self.auth_client.get(f'{endpoint}?user_services_info__industries={self.industry1.pk}&user_services_info__industries={self.industry2.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(20, len(resp.json()['results']))

    def test_list_service_type_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?user_services_info__services__service_type={self.service_type.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_service_type_filter_2(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?&user_services_info__services__service_type={self.service_type2.pk}', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_price_ordering(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?ordering=services__price', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['results'][0]['price_start'] <= resp.json()['results'][1]['price_start'])
        self.assertTrue(resp.json()['results'][0]['price_start'] <= resp.json()['results'][19]['price_start'])

    def test_list_desc_price_ordering(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?ordering=-services__price', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['results'][0]['price_start'] >= resp.json()['results'][1]['price_start'])
        self.assertTrue(resp.json()['results'][0]['price_start'] >= resp.json()['results'][19]['price_start'])

    def test_list_followers_to_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?followers_to=10000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(10, len(resp.json()['results']))

    def test_list_followers_from_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?followers_from=10000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(11, len(resp.json()['results']))

    def test_list_followers_filter(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?followers_from=10000&followers_to=15000', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(6, len(resp.json()['results']))

    def test_list_followers_ordering(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?ordering=user_services_info__followers', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['results'][0]['followers'] <= resp.json()['results'][1]['followers'])
        self.assertTrue(resp.json()['results'][0]['followers'] <= resp.json()['results'][19]['price_start'])

    def test_list_desc_followers_ordering(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(f'{endpoint}?ordering=-user_services_info__followers', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['results'][0]['followers'] >= resp.json()['results'][1]['followers'])
        self.assertTrue(resp.json()['results'][0]['followers'] >= resp.json()['results'][19]['followers'])


class ServicesTestCase(TestCase):
    def setUp(self):
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
        self.country = Country.objects.create(name='Country')
        self.work_city = WorkCityProxy.objects.create(
            name='WorkCity1',
            country=self.country
        )
        self.work_city2 = WorkCityProxy.objects.create(
            name='WorkCity2',
            country=self.country
        )
        self.users = []
        user_group = auth_models.Group.objects.get(name='User')
        investor_group = auth_models.Group.objects.get(name='Investor')
        for i in range(1, 21):
            user = user_models.User.objects.create(
                email=f'test{i}@email.com',
                name='ftest ltest',
                is_approved=True
            )
            self.users.append(user)
            BankDetails.objects.create(
                user=user,
                membership='premium'
            )
            user_service_info = models.UserServiceInfo.objects.create(
                user=user,
                professional_service_provider=True,
                generate_business=True,
                followers=i * 1000
            )
            user.groups.add(user_group)
            if i > 10:
                user_models.Profile.objects.create(
                    user=user,
                    name='Profile',
                    work_city=self.work_city2
                )
                user_service_info.industries.add(self.industry1)
                s1 = models.Service.objects.create(
                    service_type=self.service_type,
                    user=user,
                    status='approved',
                    price_type='price',
                    price=i * 200,
                    rating=i * 0.1,
                    timeline=60,
                    attachments=[],
                    questions=[]
                )
            else:
                user_models.Profile.objects.create(
                    user=user,
                    name='Profile',
                    work_city=self.work_city
                )
                s1 = models.Service.objects.create(
                    service_type=self.service_type2,
                    user=user,
                    status='approved',
                    price_type='price',
                    price=i * 200,
                    rating=i * 0.1,
                    timeline=60,
                    attachments=[],
                    questions=[]
                )
                user_service_info.industries.add(self.industry2)
            user_service_info.services.add(s1)
        self.investors = []
        for i in range(1, 5):
            user = user_models.User.objects.create(
                email=f'test{i+20}@email.com',
                name='ftest ltest',
                is_approved=True
            )
            self.users.append(user)
            BankDetails.objects.create(
                user=user,
                membership='premium'
            )
            investor_info = models.InvestorServiceInfo.objects.create(
                process='asdasd',
                attachments=['asd', 'asdasd'],
                questions=['asdasdasd', 'asdadqw123'],
                understand=True,
                reach_out=True,
                user=user
            )
            user.groups.add(investor_group)
            self.investors.append(user)

        self.user = user_models.User.objects.create(
            email='test@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user.set_password('Qwer1234!')
        self.user.save()
        self.token = jwt_encode(self.user)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'user_service_detail': lambda x: reverse('v1:services:user-service-detail', kwargs={'pk': x}),
            'investor_service_detail': lambda x: reverse('v1:services:investor-service-detail', kwargs={'pk': x}),
        }

    def test_user_service_detail(self):
        endpoint = self.endpoints.get('user_service_detail')(self.users[0].pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)

    def test_investor_service_detail(self):
        endpoint = self.endpoints.get('investor_service_detail')(self.investors[0].pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
