from unittest import mock

from django.core.files import File
from django.test import TestCase, Client

from django.urls import reverse
from rest_auth.utils import jwt_encode

from creative_exchange.models import ExchangeRequest, ExchangeCategory
from locations.models import Country
from order import models
from services import models as services_models
from tags.models import Industry, WorkCityProxy
from users import models as user_models
from utils import file_test_service


class QuoteTestCase(TestCase):
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
        self.auth_buyer = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        seller_token = jwt_encode(self.user)
        self.auth_seller = Client(HTTP_AUTHORIZATION=f'JWT {seller_token}')
        self.endpoints = {
            'quote-buyer-list': reverse('v1:orders:quote-buyer-list'),
            'quote-buyer-detail': lambda x: reverse('v1:orders:quote-buyer-detail', kwargs={'pk': x}),
            'quote-buyer-accept': lambda x: reverse('v1:orders:quote-buyer-accept', kwargs={'pk': x}),
            'quote-buyer-cancel': lambda x: reverse('v1:orders:quote-buyer-cancel', kwargs={'pk': x}),
            'quote-seller-list': reverse('v1:orders:quote-seller-list'),
            'quote-seller-detail': lambda x: reverse('v1:orders:quote-seller-detail', kwargs={'pk': x}),
            'quote-seller-cancel': lambda x: reverse('v1:orders:quote-seller-cancel', kwargs={'pk': x}),
            'quote-seller-provide': lambda x: reverse('v1:orders:quote-seller-provide', kwargs={'pk': x})
        }
        self.quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service
        )
        self.attachment = models.Attachment.objects.create(
            name='Attachment',
            quote=self.quote
        )
        self.answer2 = models.Answer.objects.create(
            question='1',
            text='1-text',
            quote=self.quote
        )
        self.answer1 = models.Answer.objects.create(
            question='2',
            text='2-text',
            quote=self.quote
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
        endpoint = self.endpoints.get('quote-buyer-list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_quote_buyer_list_success_buyer(self):
        endpoint = self.endpoints.get('quote-buyer-list')
        resp = self.auth_buyer.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_get_quote_buyer_list_success_seller(self):
        endpoint = self.endpoints.get('quote-buyer-list')
        resp = self.auth_seller.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.json()['results']))

    def test_get_quote_seller_list_success_buyer(self):
        endpoint = self.endpoints.get('quote-seller-list')
        resp = self.auth_buyer.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.json()['results']))

    def test_get_quote_seller_list_success_seller(self):
        endpoint = self.endpoints.get('quote-seller-list')
        resp = self.auth_seller.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_post_successful(self):
        endpoint = self.endpoints.get('quote-buyer-list')
        data = {
            'seller': self.user.pk,
            'service': self.service.pk,
            'answers': [
                {'question': '1', 'text': '213'}
            ],
            'attachments': [
                {
                    'name': '1',
                    'files_base64': [
                        file_test_service.get_test_base64_image(),
                        file_test_service.get_test_base64_image()
                    ]
                }
            ],
            'date_preferences': [
                {
                    'date': '2020-11-11',
                    'time_start': '11:00',
                    'time_end': '15:00'
                }
            ]
        }
        resp = self.auth_buyer.post(endpoint, data, content_type='application/json')
        self.assertEqual(201, resp.status_code)
        self.assertTrue(resp.json()['service'])
        self.assertEqual(1, len(resp.json()['attachments']))
        self.assertEqual(1, len(resp.json()['answers']))
        self.assertEqual(1, len(resp.json()['date_preferences']))

    def test_get_quote_buyer_list_success_buyer_ordering(self):
        endpoint = self.endpoints.get('quote-buyer-list')
        quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='canceled'
        )
        quote_provided = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='provided'
        )
        resp = self.auth_buyer.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(3, len(resp.json()['results']))
        self.assertEqual('pending', resp.json()['results'][0]['status'])
        self.assertEqual('provided', resp.json()['results'][1]['status'])
        self.assertEqual('canceled', resp.json()['results'][2]['status'])

    def test_post_quote_buyer_accept(self):
        quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='provided'
        )
        endpoint = self.endpoints.get('quote-buyer-accept')(quote.pk)
        data = {}
        resp = self.auth_buyer.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertIn('order_pk', resp.json())
        self.assertTrue(resp.json()['order_pk'])

    def test_post_quote_buyer_cancel(self):
        quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='provided'
        )
        endpoint = self.endpoints.get('quote-buyer-cancel')(quote.pk)
        data = {}
        resp = self.auth_buyer.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        quote.refresh_from_db()
        self.assertEqual('canceled', quote.status)

    def test_post_quote_seller_cancel(self):
        quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='pending'
        )
        endpoint = self.endpoints.get('quote-seller-cancel')(quote.pk)
        data = {}
        resp = self.auth_seller.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        quote.refresh_from_db()
        self.assertEqual('canceled', quote.status)

    def test_post_quote_seller_provide(self):
        quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='pending'
        )
        endpoint = self.endpoints.get('quote-seller-provide')(quote.pk)
        data = {
            'comment': 'Comment',
            'price': 1000,
            'timeline': 10,
            'revisions': 5,
            'note': 'NoteText',
        }
        resp = self.auth_seller.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        quote.refresh_from_db()
        self.assertEqual('provided', quote.status)
        self.assertEqual('Comment', quote.comment)
        self.assertEqual(1000, quote.price)
        self.assertEqual(10, quote.timeline)
        self.assertEqual(5, quote.revisions)
        self.assertEqual('NoteText', quote.note)


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
            'funding-request-detail': lambda x: reverse('v1:orders:funding-request-buyer-detail', kwargs={'pk': x}),
            'funding-investor-list': reverse('v1:orders:funding-request-investor-list'),
            'funding-investor-detail': lambda x: reverse('v1:orders:funding-request-investor-detail', kwargs={'pk': x}),
            'funding-accept': lambda x: reverse('v1:orders:funding-request-investor-accept', kwargs={'pk': x}),
            'funding-cancel': lambda x: reverse('v1:orders:funding-request-investor-cancel', kwargs={'pk': x}),
        }
        investor_token = jwt_encode(self.user)
        self.auth_investor = Client(HTTP_AUTHORIZATION=f'JWT {investor_token}')

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

    def test_get_funding_list_fail_unauth(self):
        endpoint = self.endpoints.get('funding-request-list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_funding_list_success(self):
        endpoint = self.endpoints.get('funding-request-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_post_funding_success(self):
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

    def test_get_investor_list_empty(self):
        endpoint = self.endpoints.get('funding-investor-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual([], resp.json()['results'])

    def test_get_investor_list(self):
        endpoint = self.endpoints.get('funding-investor-list')
        resp = self.auth_investor.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_get_investor_detail_success(self):
        endpoint = self.endpoints.get('funding-investor-detail')(self.funding_request.pk)
        resp = self.auth_investor.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)

    def test_get_detail_success(self):
        endpoint = self.endpoints.get('funding-request-detail')(self.funding_request.pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)

    def test_post_cancel_request_fail_wrong_user(self):
        endpoint = self.endpoints.get('funding-cancel')(self.funding_request.pk)
        resp = self.auth_client.post(endpoint, content_type='application/json')
        self.assertEqual(404, resp.status_code)

    def test_post_cancel_request_success(self):
        endpoint = self.endpoints.get('funding-cancel')(self.funding_request.pk)
        resp = self.auth_investor.post(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.funding_request.refresh_from_db()
        self.assertEqual('canceled', self.funding_request.status)

    def test_post_accept_request_fail_wrong_user(self):
        endpoint = self.endpoints.get('funding-accept')(self.funding_request.pk)
        resp = self.auth_client.post(endpoint, content_type='application/json')
        self.assertEqual(404, resp.status_code)

    def test_post_accept_request_success(self):
        endpoint = self.endpoints.get('funding-accept')(self.funding_request.pk)
        resp = self.auth_investor.post(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.funding_request.refresh_from_db()
        self.assertEqual('accepted', self.funding_request.status)


    def test_list_ordering(self):
        funding_request_canceled = models.FundingRequest.objects.create(
            buyer=self.user2,
            investor=self.user,
            status='canceled'
        )
        funding_request_accepted = models.FundingRequest.objects.create(
            buyer=self.user2,
            investor=self.user,
            status='accepted'
        )
        endpoint = self.endpoints.get('funding-request-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(3, len(resp.json()['results']))
        self.assertEqual('pending', resp.json()['results'][0]['status'])
        self.assertEqual('accepted', resp.json()['results'][1]['status'])
        self.assertEqual('canceled', resp.json()['results'][2]['status'])


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
        self.auth_buyer = Client(HTTP_AUTHORIZATION=f'JWT {self.token}')
        self.endpoints = {
            'order-buyer-list': reverse('v1:orders:order-buyer-list'),
            'order-buyer-detail': lambda x: reverse('v1:orders:order-buyer-detail', kwargs={'pk': x}),
            'order-buyer-add-review': lambda x: reverse('v1:orders:order-buyer-add-review', kwargs={'pk': x}),
            'order-seller-list': reverse('v1:orders:order-seller-list'),
            'order-seller-detail': lambda x: reverse('v1:orders:order-seller-detail', kwargs={'pk': x}),
            'order-seller-accept': lambda x: reverse('v1:orders:order-seller-accept', kwargs={'pk': x}),
            'order-seller-cancel': lambda x: reverse('v1:orders:order-seller-cancel', kwargs={'pk': x}),
            'order-cart-list': reverse('v1:orders:order-cart-list'),
            'order-cart-detail': lambda x: reverse('v1:orders:order-cart-detail', kwargs={'pk': x}),
        }
        seller_token = jwt_encode(self.user)
        self.auth_seller = Client(HTTP_AUTHORIZATION=f'JWT {seller_token}')
        self.order = models.Order.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='pending'
        )
        self.order2 = models.Order.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service
        )
        self.attachment = models.Attachment.objects.create(
            name='Attachment',
            order=self.order
        )
        self.answer2 = models.Answer.objects.create(
            question='1',
            text='1-text',
            order=self.order
        )
        self.answer1 = models.Answer.objects.create(
            question='2',
            text='2-text',
            order=self.order
        )
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'
        self.attachment_file = models.AttachmentFile(
            attachment=self.attachment,
            file=file_mock
        )

    def test_success_setup(self):
        self.assertEqual(1, 1)

    def test_get_order_list_fail_unauth(self):
        endpoint = self.endpoints.get('order-buyer-list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_order_buyer_list_success_buyer(self):
        endpoint = self.endpoints.get('order-buyer-list')
        resp = self.auth_buyer.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_get_order_buyer_list_success_seller(self):
        endpoint = self.endpoints.get('order-buyer-list')
        resp = self.auth_seller.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.json()['results']))

    def test_get_order_seller_list_success_buyer(self):
        endpoint = self.endpoints.get('order-seller-list')
        resp = self.auth_buyer.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.json()['results']))

    def test_get_order_seller_list_success_seller(self):
        endpoint = self.endpoints.get('order-seller-list')
        resp = self.auth_seller.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_post_order_seller_accept(self):
        endpoint = self.endpoints.get('order-seller-accept')(self.order.pk)
        data = {}
        resp = self.auth_seller.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('accepted', resp.json()['status'])

    def test_post_order_seller_cancel(self):
        endpoint = self.endpoints.get('order-seller-cancel')(self.order.pk)
        data = {}
        resp = self.auth_seller.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('canceled', resp.json()['status'])

    def test_post_order_seller_accept_with_quotes(self):
        quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service
        )
        order = models.Order.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='pending',
            quote=quote
        )
        endpoint = self.endpoints.get('order-seller-accept')(order.pk)
        data = {}
        resp = self.auth_seller.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('accepted', resp.json()['status'])
        quote.refresh_from_db()
        self.assertEqual('accepted', quote.status)

    def test_post_order_seller_accept_with_creative_quotes(self):
        category = ExchangeCategory.objects.create(name='Category')
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'
        creative_request = ExchangeRequest.objects.create(
            category=category,
            user=self.user2,
            title='Title',
            cover_image=file_mock,
            description='Text',
            special_requirement='Text',
            additional_information='Text',
            extended_price=1000,
        )
        quote = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            exchange_request=creative_request
        )
        quote2 = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            exchange_request=creative_request
        )
        quote3 = models.Quote.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            exchange_request=creative_request
        )
        order = models.Order.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='pending',
            quote=quote
        )
        endpoint = self.endpoints.get('order-seller-accept')(order.pk)
        data = {}
        resp = self.auth_seller.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('accepted', resp.json()['status'])
        quote.refresh_from_db()
        self.assertEqual('accepted', quote.status)
        quote2.refresh_from_db()
        self.assertEqual('canceled', quote2.status)
        quote3.refresh_from_db()
        self.assertEqual('canceled', quote3.status)

    def test_get_order_cart_list_success_buyer(self):
        endpoint = self.endpoints.get('order-cart-list')
        resp = self.auth_buyer.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_get_order_cart_list_success_seller(self):
        endpoint = self.endpoints.get('order-cart-list')
        resp = self.auth_seller.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, len(resp.json()['results']))

    def test_post_order_success(self):
        endpoint = self.endpoints.get('order-buyer-list')
        data = {
            'seller': self.user.pk,
            'service': self.service.pk,
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
        resp = self.auth_buyer.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(201, resp.status_code)
        self.assertTrue(resp.json()['attachments'])
        self.assertTrue(resp.json()['answers'])
        self.assertIn('pk', resp.json())
        order = models.Order.objects.get(pk=resp.json()['pk'])
        self.assertEqual('created', order.status)

    def test_add_review(self):
        order = models.Order.objects.create(
            buyer=self.user2,
            seller=self.user,
            service=self.service,
            status='accepted'
        )
        endpoint = self.endpoints.get('order-buyer-add-review')(order.pk)
        data = {
            'rate': 5,
            'review_text': 'Review text'
        }
        resp = self.auth_buyer.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('complete', resp.json()['status'])
