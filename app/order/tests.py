from unittest import mock

from django.core.files import File
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from locations.models import Country
from order import models
from services import models as services_models
from tags.models import Industry, WorkCityProxy
from users import models as user_models
from utils import file_test_service


class OrderTestCase(TestCase):
    def setUp(self):
        self.category = services_models.ProfessionalCategoryProxy.objects.create(name='Category')
        self.service_type = services_models.ServiceType.objects.create(
            name='Type', category=self.category, description='Description', group='service'
        )
        self.industry1 = Industry.objects.create(name='Industry')
        self.industry2 = Industry.objects.create(name='Industry2')
        self.country = Country.objects.create(name='Country')
        self.work_city = WorkCityProxy.objects.create(
            name='WorkCity1',
            country=self.country
        )
        self.user = user_models.User.objects.create(
            email='test@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user_service_info = services_models.UserServiceInfo.objects.create(
            user=self.user,
            professional_service_provider=True,
            generate_business=True,
            followers=1000
        )
        user_models.Profile.objects.create(
            user=self.user,
            name='Profile',
            work_city=self.work_city
        )
        self.user_service_info.industries.add(self.industry1)
        self.service = services_models.Service.objects.create(
            service_type=self.service_type,
            user=self.user,
            status='approved',
            price_type='price',
            price=200,
            rating=3.0,
            timeline=60,
            attachments=['1', '2'],
            questions=['1', '2']
        )

        self.user_service_info.services.add(self.service)
        self.user2 = user_models.User.objects.create(
            email='test1@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user2.set_password('Qwer1234!')
        self.user2.save()
        self.token = jwt_encode(self.user2)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'order-list': reverse('v1:orders:buyer-list'),
            'order-detail': lambda x: reverse('v1:orders:buyer-detail', kwargs={'pk': x})
        }

        self.order = models.Order.objects.create(
            buyer=self.user2,
            seller=self.user
        )
        self.order_service = models.OrderService.objects.create(
            order=self.order,
            service=self.service,
        )
        self.attachment = models.Attachment.objects.create(
            name='Attachment',
            order_service=self.order_service
        )
        self.answer2 = models.Answer.objects.create(
            question='1',
            text='1-text',
            order_service=self.order_service
        )
        self.answer1 = models.Answer.objects.create(
            question='2',
            text='2-text',
            order_service=self.order_service
        )
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'
        self.attachment_file = models.AttachmentFile(
            attachment=self.attachment,
            file=file_mock
        )

    def test_success_setup(self):
        self.assertEqual(1, 1)

    def test_get_list_fail_unauth(self):
        endpoint = self.endpoints.get('order-list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_list_success(self):
        endpoint = self.endpoints.get('order-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))


class FundingRequestTestCase(TestCase):
    def setUp(self):
        self.category = services_models.ProfessionalCategoryProxy.objects.create(name='Category')
        self.service_type = services_models.ServiceType.objects.create(
            name='Type', category=self.category, description='Description', group='service'
        )
        self.industry1 = Industry.objects.create(name='Industry')
        self.industry2 = Industry.objects.create(name='Industry2')
        self.country = Country.objects.create(name='Country')
        self.work_city = WorkCityProxy.objects.create(
            name='WorkCity1',
            country=self.country
        )
        self.user = user_models.User.objects.create(
            email='test@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user_service_info = services_models.UserServiceInfo.objects.create(
            user=self.user,
            professional_service_provider=True,
            generate_business=True,
            followers=1000
        )
        user_models.Profile.objects.create(
            user=self.user,
            name='Profile',
            work_city=self.work_city
        )
        self.user_service_info.industries.add(self.industry1)
        self.service = services_models.Service.objects.create(
            service_type=self.service_type,
            user=self.user,
            status='approved',
            price_type='price',
            price=200,
            rating=3.0,
            timeline=60,
            attachments=['1', '2'],
            questions=['1', '2']
        )

        self.user_service_info.services.add(self.service)
        self.user2 = user_models.User.objects.create(
            email='test1@email.com',
            name='ftest ltest',
            is_approved=True
        )
        self.user2.set_password('Qwer1234!')
        self.user2.save()
        self.token = jwt_encode(self.user2)
        self.client = Client()
        self.auth_client = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'funding-request-list': reverse('v1:orders:funding-request-buyer-list'),
            'funding-request-detail': lambda x: reverse('v1:orders:funding-request-buyer-detail', kwargs={'pk': x})
        }

        self.funding_request = models.FundingRequest.objects.create(
            buyer=self.user2,
            investor=self.user
        )
        self.attachment = models.Attachment.objects.create(
            name='Attachment',
            funding_request=self.funding_request
        )
        self.answer2 = models.Answer.objects.create(
            question='1',
            text='1-text',
            funding_request=self.funding_request
        )
        self.answer1 = models.Answer.objects.create(
            question='2',
            text='2-text',
            funding_request=self.funding_request
        )
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'
        self.attachment_file = models.AttachmentFile(
            attachment=self.attachment,
            file=file_mock
        )

    def test_success_setup(self):
        self.assertEqual(1, 1)

    def test_get_list_fail_unauth(self):
        endpoint = self.endpoints.get('funding-request-list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_list_success(self):
        endpoint = self.endpoints.get('funding-request-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_post_success(self):
        endpoint = self.endpoints.get('funding-request-list')
        data = {
            'investor': self.user.pk,
            'answers': [
                {'question': '1',  'text': '213'}
            ],
            'attachments': [
                {
                    'name': '1',
                    'files_base64': [
                        file_test_service.get_test_base64_image(),
                        file_test_service.get_test_base64_image()
                    ]
                 }
            ]
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(201, resp.status_code)
        self.assertTrue(resp.json()['attachments'])
        self.assertTrue(resp.json()['answers'])


