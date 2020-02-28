import datetime
from unittest import mock
from unittest.mock import patch

from allauth.account.models import EmailAddress, EmailConfirmation
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.auth.tokens import default_token_generator
from django.core.files import File
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_auth.utils import jwt_encode
from rest_framework import status

from locations import models as locations_models
from payment.models import BankDetails
from services import models as services_models
from tags.models import Tag, Industry, Company, Funding, CityProxy, WorkCityProxy
from users import models
from utils.file_test_service import get_test_base64_image


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
            'login': reverse('v1:users:rest_login'),
            'logout': reverse('v1:users:rest_logout'),
            'user': reverse('v1:users:rest_user_details'),
            'register': reverse('v1:users:rest_register'),
            'change-password': reverse('v1:users:rest_password_change'),
            'reset-password': reverse('v1:users:rest_password_reset'),
            'reset-password-confirm': reverse('v1:users:rest_password_reset_confirm'),
            'user-details': reverse('v1:users:rest_user_details'),
            'user-profile': reverse('v1:users:profile-list'),
            'user-phone-number-new': reverse('v1:users:verify-new-phone-number'),
            'user-send-verify-email': reverse('v1:users:verify-send-verify-email'),
            'user-verify-email': reverse('v1:users:rest_verify_email'),
            'user-check-code': reverse('v1:users:verify-check-sms-code'),
            'user-bank-details': reverse('v1:users:bank-details-list'),
            'user-services-details': reverse('v1:users:services-list'),
            'user-investor-details': reverse('v1:users:investor-services-list')
        }

        self.country = locations_models.Country.objects.create(name='Country')
        self.city = CityProxy.objects.create(name='City', country=self.country)
        self.work_city = WorkCityProxy.objects.create(name='City', country=self.country)
        self.tag = Tag.objects.create(name='Tag')

    def test_login_success(self):
        endpoint = self.endpoints.get('login')
        data = {'email': 'test@email.com', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json())

        self.assertEqual('user', resp.json()['user']['role'])

    def test_login_success_with_spaces(self):
        endpoint = self.endpoints.get('login')
        data = {'email': ' test@email.com ', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json())

    def test_login_success_email_with_camelcase(self):
        endpoint = self.endpoints.get('login')
        data = {'email': ' tesT@email.com ', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json())

    def test_login_fail_email(self):
        endpoint = self.endpoints.get('login')
        data = {'email': 'test2@email.com', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('non_field_errors', resp.json())
        self.assertEqual('Email or password is not correct', resp.json()['non_field_errors'][0])

    def test_login_fail_empty_email(self):
        endpoint = self.endpoints.get('login')
        data = {'email': '', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('email', resp.json())
        self.assertEqual(['Please enter your email'], resp.json()['email'])

    def test_login_fail_empty_password(self):
        endpoint = self.endpoints.get('login')
        data = {'email': 'test@user.com', 'password': ''}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('password', resp.json())
        self.assertEqual(['Please enter the password'], resp.json()['password'])

    def test_login_fail_email_frong_format(self):
        endpoint = self.endpoints.get('login')
        data = {'email': 'test2', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('email', resp.json())
        self.assertEqual(['Please enter a valid email'], resp.json()['email'])

    def test_login_fail_email_too_long(self):
        endpoint = self.endpoints.get('login')
        data = {'email': f'{"test"*40}@email.com', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('email', resp.json())
        self.assertEqual(['Please enter a valid email'], resp.json()['email'])

    def test_login_fail_password(self):
        endpoint = self.endpoints.get('login')
        data = {'email': 'test@email.com', 'password': 'Qwer1234!@'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('non_field_errors', resp.json())

    @mock.patch('users.models.User.send_verify_email', return_value=None)
    def test_success_register(self, send_verify_email):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': 'Testy User'}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(data.get('name'), resp.json()['user']['name'])
        self.assertEqual(data.get('email'), resp.json()['user']['email'])
        self.assertIn('token', resp.json())
        user = models.User.objects.get(email='test1@email.com')
        self.assertIn('User', list(user.groups.values_list('name', flat=True)))

    @mock.patch('users.models.User.send_verify_email', return_value=None)
    def test_success_register_subs(self, send_verify_email):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': 'Testy User'}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        if timezone.now().date() < datetime.date(2020, 12, 1):
            self.assertTrue(resp.json()['user']['has_active_subscription'])

    @mock.patch('users.models.User.send_email', return_value=None)
    def test_success_send_verify_email(self, send_email):
        endpoint = self.endpoints.get('user-send-verify-email')
        resp = self.auth_client.post(endpoint, data={}, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertTrue(send_email.called)

    @mock.patch('users.models.User.send_email', return_value=None)
    def test_success_verify_email_fail(self, send_email):
        endpoint = self.endpoints.get('user-verify-email')
        self.user.send_verify_email()
        self.assertTrue(send_email.called)
        resp = self.auth_client.post(endpoint, data={'key': 'not valid key'}, content_type='application/json')
        self.assertEqual(400, resp.status_code)

    @mock.patch('users.models.User.send_email', return_value=None)
    def test_success_verify_email_success(self, send_email):
        endpoint = self.endpoints.get('user-verify-email')
        self.user.send_verify_email()
        self.assertTrue(send_email.called)
        email_address = EmailAddress.objects.get(user=self.user, email=self.user.email, verified=False)
        key = EmailConfirmation.objects.filter(email_address=email_address).first().key
        resp = self.auth_client.post(endpoint, data={'key': key}, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    @mock.patch('users.models.User.send_verify_email', return_value=None)
    def test_success_register_investor(self, send_verify_email):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': 'Testy User', 'role': 'investor'}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(data.get('name'), resp.json()['user']['name'])
        self.assertEqual(data.get('email'), resp.json()['user']['email'])
        self.assertIn('token', resp.json())
        user = models.User.objects.get(email='test1@email.com')
        self.assertIn('Investor', list(user.groups.values_list('name', flat=True)))

    def test_fail_register_empty_name(self):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': ''}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('name', resp.json())
        self.assertEqual(['Please enter your name'], resp.json()['name'])

    def test_fail_register_email_exists(self):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test@email.com', 'password': 'Qwer1234!', 'name': 'Testy'}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('email', resp.json())
        self.assertEqual(['This email is already registered, sign in instead'], resp.json()['email'])

    def test_fail_register_name_too_long(self):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': 'name'*40}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('name', resp.json())
        self.assertEqual(['Please enter the valid name'], resp.json()['name'])

    @mock.patch('users.models.User.send_verify_email', return_value=None)
    def test_register_success_email_with_camelcase(self, send_verify_email):
        endpoint = self.endpoints.get('register')
        data = {'email': ' tesTy@email.com ', 'password': 'Qwer1234!', 'name': 'name'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertIn('token', resp.json())

    def test_register_fail_email(self):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test@email.com', 'password': 'Qwer1234!', 'name': 'name'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('email', resp.json())
        self.assertEqual(['This email is already registered, sign in instead'], resp.json()['email'])

    def test_register_fail_empty_email(self):
        endpoint = self.endpoints.get('register')
        data = {'email': '', 'password': 'Qwer1234!', 'name': 'name'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('email', resp.json())
        self.assertEqual(['Please enter your email'], resp.json()['email'])

    def test_change_password_success(self):
        endpoint = self.endpoints.get('change-password')
        data = {'old_password': 'Qwer1234!', 'new_password': 'Qwer1234!2'}
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('detail', resp.json())

    def test_change_password_fail_wrong_old_password(self):
        endpoint = self.endpoints.get('change-password')
        data = {'old_password': 'Qwer123', 'new_password': 'Qwer1234!2'}
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('old_password', resp.json())

    @patch('users.models.User.send_reset_password_email', autospec=True)
    def test_reset_password(self, send_email):
        endpoint = self.endpoints.get('reset-password')
        data = {'email': 'test@email.com'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(send_email.called)

    @patch('users.models.User.send_reset_password_email', autospec=True)
    def test_reset_password_wrong_email(self, send_email):
        endpoint = self.endpoints.get('reset-password')
        data = {'email': 'testy@email.com'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(send_email.called)

    def test_reset_password_confirm(self):
        endpoint = self.endpoints.get('reset-password-confirm')
        data = {
            'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
            'token': default_token_generator.make_token(self.user),
            'new_password': 'Qwer1234!'
        }
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)

    def test_reset_password_confirm_fail_less_symbols(self):
        endpoint = self.endpoints.get('reset-password-confirm')
        data = {
            'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
            'token': default_token_generator.make_token(self.user),
            'new_password': 'Qwer12'
        }
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('new_password', resp.json())

    def test_reset_password_confirm_fail_only_letters(self):
        endpoint = self.endpoints.get('reset-password-confirm')
        data = {
            'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
            'token': default_token_generator.make_token(self.user),
            'new_password': 'Qwer'
        }
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('new_password', resp.json())

    def test_change_user_city_fail_unauth(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'city': self.city.pk
        }
        resp = self.client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_change_user_city(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'city': self.city.pk
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.city, self.city)

    def test_reason_user_change_join(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'reason': 'join'
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.reason, 'join')

    def test_reason_user_change_18_year_old(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'reason': '18_year_old'
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.reason, '18_year_old')

    def test_reason_user_change_understand(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'reason': 'understand'
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.reason, 'understand')

    def test_reason_user_change_success(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'reason': '123123'
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('reason', resp.json())

    def test_has_profile(self):
        self.assertFalse(self.user.has_profile)
        self.assertFalse(self.user.full_registered)

    def test_has_bank_details(self):
        self.assertFalse(self.user.has_bank_details)
        self.assertFalse(self.user.full_registered)

    def test_has_services(self):
        self.assertFalse(self.user.has_services)
        self.assertFalse(self.user.full_registered)

    def test_user_details_fail_unauth(self):
        endpoint = self.endpoints.get('user-details')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_user_details_success(self):
        endpoint = self.endpoints.get('user-details')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = {
            'pk': str(self.user.pk),
            'email': self.user.email,
            'email_verified': False,
            'name': self.user.name,
            'reason': None,
            'city': None,
            'full_registered': False,
            'has_profile': False,
            'has_bank_details': False,
            'has_services': False,
            'has_active_subscription': True,
            'active_subscription_membership': 'basic',
            'phone_number': '',
            'phone_number_verified': False,
            'role': 'user',
            'pan_card': None,
            'pan_card_size': None,
        }
        self.assertDictEqual(data, resp.json())


    def test_user_patch_details_fail(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'city': ''
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_user_patch_details_fail_2(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'city': None
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_user_patch_details_success_3(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'name': 'New Name'
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)

    def test_user_patch_details_success_4(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'pan_card_base64': get_test_base64_image()
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['pan_card'])

    def test_profile_get_fail_unauth(self):
        endpoint = self.endpoints.get('user-profile')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_profile_get_fail_not_found(self):
        endpoint = self.endpoints.get('user-profile')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 404)

    def test_profile_get_success(self):
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city
        )
        endpoint = self.endpoints.get('user-profile')
        data = {
            'name': 'Testy',
            'tag_list': [],
            'tag_line': '',
            'cover': None,
            'cover_file': None,
            'photo': None,
            'introduction': '',
            'is_cover_video': False,
            'focus': '',
            'is_instagram_set': False,
            'instagram_username': None,
            'twitter': '',
            'additional_information': '',
            'work_city': city.pk,
            'work_city_name': city.name,
            'public_profile': True,
            'cover_transcoder': None,
            'cover_thumbnail': None
        }
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        result = resp.json()
        result.pop('pk')
        result.pop('uuid')
        self.assertDictEqual(data, result)

    @patch('users.models.User.send_sms', autospec=True)
    def test_set_phone_number_fail_blank(self, send_sms):
        endpoint = self.endpoints.get('user-phone-number-new')
        data = {
            'phone_number': ''
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    @patch('users.models.User.send_sms', autospec=True)
    def test_set_phone_number_success_resend(self, send_sms):
        endpoint = self.endpoints.get('user-phone-number-new')
        self.user.phone_number = '+380999999999'
        self.user.save()
        data = {}
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '+380999999999')
        self.assertFalse(self.user.phone_number_verified)
        self.assertTrue(send_sms.called)

    @patch('users.models.User.send_sms', autospec=True)
    def test_set_phone_number(self, send_sms):
        endpoint = self.endpoints.get('user-phone-number-new')
        data = {
            'phone_number': '+380999999999'
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '+380999999999')
        self.assertFalse(self.user.phone_number_verified)
        self.assertTrue(send_sms.called)

    @override_settings(DEBUG=True)
    @patch('users.models.User.send_sms', autospec=True)
    def test_change_phone_number(self, send_sms):
        endpoint = self.endpoints.get('user-phone-number-new')
        self.user.phone_number = '+380998888888'
        self.user.save()
        data = {
            'phone_number': '+380999999999'
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '+380999999999')
        self.assertFalse(self.user.phone_number_verified)
        self.assertTrue(self.user.sms_code)
        self.assertTrue(send_sms.called)
        data = {
            'sms_code': '1111'
        }
        endpoint = self.endpoints.get('user-check-code')
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '+380999999999')
        self.assertTrue(self.user.phone_number_verified)
        self.assertFalse(self.user.sms_code)

    @patch('users.models.User.send_sms', autospec=True)
    def test_resend_sms_code(self, send_sms):
        endpoint = self.endpoints.get('user-phone-number-new')
        self.user.phone_number = '+380998888888'
        self.user.sms_code = sms_code = '2222'
        self.user.save()
        data = {
            'phone_number': '+380998888888'
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.sms_code, sms_code)
        self.assertTrue(send_sms.called)

    @patch('utils.transcoder_service.TranscoderService.create_file_transcoder_job', autospec=True)
    def test_profile_set_success(self, create_file_transcoder_job):
        endpoint = self.endpoints.get('user-profile')
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'

        cover_file = models.CoverFile.objects.create(file=file_mock, user=self.user)
        data = {
            'name': 'Test',
            'tags': [self.tag.pk],
            'tag_line': '',
            'cover': cover_file.pk,
            'photo': None,
            'introduction': '',
            'focus': '',
            'additional_information': '',
            'work_city': city.pk
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_profile)

    @patch('utils.instagram_service.InstagramService.convert_code_to_long_access_token', autospec=True, return_value='Token')
    @patch('utils.transcoder_service.TranscoderService.create_file_transcoder_job', autospec=True)
    def test_profile_set_success_full_info(self, create_file_transcoder_job, convert):
        endpoint = self.endpoints.get('user-profile')
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'

        cover_file = models.CoverFile.objects.create(file=file_mock, user=self.user)
        data = {
            'name': 'Test',
            'tags': [self.tag.pk],
            'tag_line': '',
            'photo': None,
            'cover': cover_file.pk,
            'introduction': 'Introduction',
            'is_cover_video': False,
            'focus': 'Focus',
            'additional_information': 'Information',
            'work_city': city.pk,
            'work_city_name': city.name,
            'is_instagram_set': True,
            'instagram_username': 'Fake',
            'instagram': 'fake_code',
            'twitter': 'https://twitter.com/',
            'public_profile': True,
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_profile)
        data.pop('tags')
        data.pop('instagram')
        data['tag_list'] = [{'name': self.tag.name, 'pk': self.tag.pk}]
        result = resp.json()
        result.pop('pk')
        result.pop('uuid')
        cover_file_url = result.pop('cover_file')
        self.assertTrue(cover_file_url)
        data.update({'cover_transcoder': None, 'cover_thumbnail': []})
        self.assertDictEqual(data, result)

    @patch('utils.transcoder_service.TranscoderService.create_file_transcoder_job', autospec=True)
    def test_profile_change_success(self, create_file_transcoder_job):
        endpoint = self.endpoints.get('user-profile')
        models.Profile.objects.create(
            user=self.user,
            name='Testy'
        )
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        file_mock = mock.MagicMock(spec=File)
        file_mock.name = 'test.jpg'

        cover_file = models.CoverFile.objects.create(file=file_mock, user=self.user)
        data = {
            'name': 'Test',
            'introduction': 'Introduction',
            'focus': 'Focus',
            'additional_information': 'Additional Information',
            'work_city': city.pk,
            'tags': [self.tag.pk],
            'photo': get_test_base64_image(),
            'cover': cover_file.pk
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual('Testy', self.user.profile.name)
        self.assertEqual('Test', self.user.profile.name)
        self.assertEqual('Introduction', self.user.profile.introduction)
        self.assertEqual('Focus', self.user.profile.focus)
        self.assertEqual('Additional Information', self.user.profile.additional_information)
        self.assertEqual(city.pk, self.user.profile.work_city.pk)
        self.assertIn(self.tag, self.user.profile.tags.all())

    def test_device_creation_success(self):
        endpoint = self.endpoints.get('login')
        data = {'email': 'test@email.com', 'password': 'Qwer1234!', 'os_id': 'testy_os_id'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(1, self.user.devices.filter(is_active=True).count())

    def test_logout_device_deactivate(self):
        endpoint = self.endpoints.get('logout')
        data = {'os_id': 'testy_os_id'}
        models.Device.objects.create(user=self.user, os_id='testy_os_id')
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(1, self.user.devices.filter(is_active=False).count())

    def test_logout_fail_method_not_allowed(self):
        endpoint = self.endpoints.get('logout')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 405)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('utils.twilio_service.TwilioService.send_message', autospec=True)
    def test_send_sms_success(self, send_message):
        self.user._send_sms('1111', 'message')
        self.assertTrue(send_message.called)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('utils.one_signal_service.OneSignalService.send_push', autospec=True)
    def test_send_push_success(self, send_push):
        models.Device.objects.create(user=self.user, os_id='testy_os_id')

        self.user.send_push({'key': 'value'}, 'message')
        self.assertTrue(send_push.called)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('utils.one_signal_service.OneSignalService.send_push', autospec=True)
    def test_send_push_success_inactive_devices(self, send_push):
        models.Device.objects.create(user=self.user, os_id='testy_os_id', is_active=False)
        self.user.refresh_from_db()
        self.user.send_push({'key': 'value'}, 'message')
        self.assertFalse(send_push.called)

    def test_bank_details_get_fail_unauth(self):
        endpoint = self.endpoints.get('user-bank-details')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_bank_details_get_fail_not_found(self):
        endpoint = self.endpoints.get('user-bank-details')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 404)

    def test_bank_details_get_success(self):
        BankDetails.objects.create(
            user=self.user,
            membership='basic',
            terms_and_condition=True
        )

        endpoint = self.endpoints.get('user-bank-details')
        data = {
            'membership': 'basic',
            'terms_and_condition': True,
            'card_data': None,
            'bank_account_name': None,
            'bank_account_number': None,
            'bank_ifsc_code': None,
            'bank_name': None,
            'branch_name': None,
            'funds_recipient': 'individual',
            'pan_card_number': None,
        }
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(data, resp.json())

    @patch('utils.stripe_service.stripe_service.create_token_charge', autospec=True, return_value='Charge')
    @patch('utils.stripe_service.stripe_service.get_customer_id', autospec=True, return_value='customer_id')
    @patch('utils.stripe_service.stripe_service.get_customer_card_data', autospec=True, return_value={'a': 'a'})
    def test_bank_details_post_success(self, create_token_charge, get_customer_id, get_customer_card_data):
        endpoint = self.endpoints.get('user-bank-details')
        data = {
            'membership': 'basic',
            'terms_and_condition': True,
            'stripe_token': 'fake_token',
            'remember_card': True,
            'bank_account_name': 'Acc name',
            'bank_account_number': 'number',
            'bank_ifsc_code': 'code',
            'bank_name': 'Bank Name',
            'branch_name': 'Branch Name',
            'funds_recipient': 'individual',
            'pan_card_number': 'card number',
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(get_customer_id.called)
        self.assertTrue(get_customer_card_data.called)
        self.user.refresh_from_db()
        self.assertDictEqual({'a': 'a'}, self.user.bank_details.card_data)
        self.assertEqual('customer_id', self.user.bank_details.stripe_customer_id)

    @patch('utils.stripe_service.stripe_service.get_customer_card_data', autospec=True, return_value=None)
    def test_bank_details_post_success_without_stripe(self, get_customer_card_data):
        endpoint = self.endpoints.get('user-bank-details')
        data = {
            'membership': 'basic',
            'terms_and_condition': True
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(get_customer_card_data.called)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.bank_details.card_data)
        self.assertIsNone(self.user.bank_details.stripe_customer_id)

    def test_network_people_authentication_required(self):
        url = reverse('v1:users:network')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_network_people_list(self):
        self.user.is_approved = True
        self.user.save(update_fields=['is_approved'])
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city,
            introduction='Introduction'
        )
        url = reverse('v1:users:network')
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        person = response.data['results'][0]
        self.assertEqual(person['name'], 'Testy')
        self.assertEqual(person['introduction'], 'Introduction')

    def test_network_people_filter_by_tag(self):
        self.user.is_approved = True
        self.user.save(update_fields=['is_approved'])
        user2 = models.User.objects.create(
            email='user2@email.com',
            name='User 2',
            is_approved=True
        )
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city,
            introduction='Introduction',
        )
        profile2 = models.Profile.objects.create(
            user=user2,
            name='Test 2',
            work_city=city,
            introduction='Introduction 2',
        )
        profile2.tags.add(self.tag)
        url = reverse('v1:users:network')
        response = self.auth_client.get(f'{url}?tags={self.tag.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        person = response.data['results'][0]
        self.assertEqual(person['name'], 'Test 2')
        self.assertEqual(person['introduction'], 'Introduction 2')

    def test_network_people_filter_by_tag_and_search(self):
        self.user.is_approved = True
        self.user.save(update_fields=['is_approved'])
        user2 = models.User.objects.create(
            email='user2@email.com',
            name='User 2',
            is_approved=True
        )
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city,
            introduction='Introduction',
        )
        profile2 = models.Profile.objects.create(
            user=user2,
            name='Test 2',
            work_city=city,
            introduction='Introduction 2',
        )
        profile2.tags.add(self.tag)
        url = reverse('v1:users:network')
        response = self.auth_client.get(f'{url}?tags={self.tag.pk}&search=test 2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        person = response.data['results'][0]
        self.assertEqual(person['name'], 'Test 2')
        self.assertEqual(person['introduction'], 'Introduction 2')

    def test_network_people_filter_by_tag_and_search_not_found(self):
        self.user.is_approved = True
        self.user.save(update_fields=['is_approved'])
        user2 = models.User.objects.create(
            email='user2@email.com',
            name='User 2',
            is_approved=True
        )
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city,
            introduction='Introduction',
        )
        profile2 = models.Profile.objects.create(
            user=user2,
            name='Test 2',
            work_city=city,
            introduction='Introduction 2',
        )
        profile2.tags.add(self.tag)
        url = reverse('v1:users:network')
        response = self.auth_client.get(f'{url}?tags={self.tag.pk}&search=wrong')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_other_profile_authentication_required(self):
        url = reverse('v1:users:other-profile', args=(1,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_network_people_detail_other_profile(self):
        self.user.is_approved = True
        self.user.save(update_fields=['is_approved'])
        user2 = models.User.objects.create(
            email='user2@email.com',
            name='User 2',
            is_approved=True
        )
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city,
            introduction='Introduction',
        )
        profile2 = models.Profile.objects.create(
            user=user2,
            name='Test 2',
            work_city=city,
            introduction='Introduction 2',
        )
        url = reverse('v1:users:other-profile', args=(user2.pk,))
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test 2')
        self.assertEqual(response.data['introduction'], 'Introduction 2')

    def test_network_people_detail_other_profile_not_found(self):
        self.user.is_approved = True
        self.user.save(update_fields=['is_approved'])
        user2 = models.User.objects.create(
            email='user2@email.com',
            name='User 2',
            is_approved=True
        )
        city = WorkCityProxy.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city,
            introduction='Introduction',
        )
        profile2 = models.Profile.objects.create(
            user=user2,
            name='Test 2',
            work_city=city,
            introduction='Introduction 2',
        )
        url = reverse('v1:users:other-profile', args=(profile2.pk,))
        profile2.delete()
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_services_get_fail_unauth(self):
        endpoint = self.endpoints.get('user-services-details')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_user_services_get_fail_no_data(self):
        endpoint = self.endpoints.get('user-services-details')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(404, resp.status_code)

    def test_user_services_get_success(self):
        endpoint = self.endpoints.get('user-services-details')
        services_models.UserServiceInfo.objects.create(
            user=self.user
        )
        data = {
            'years_of_experience': None,
            'bar_council': None,
            'followers': None,
            'industries': [],
            'services': [],
            'generate_business': False,
            'professional_service_provider': False
        }
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertDictEqual(data, resp.json())

    def test_user_services_post_success_without_services(self):
        endpoint = self.endpoints.get('user-services-details')
        industry = Industry.objects.create(name='Industry')
        industry2 = Industry.objects.create(name='Industry2')
        data = {
            'years_of_experience': 'less_1_year',
            'bar_council': 'text',
            'followers': 100,
            'industries': [industry.pk, industry2.pk],
            'services': [],
            'generate_business': False,
            'professional_service_provider': False
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertDictEqual(data, resp.json())

    def test_user_services_post_success_without_services_empty_industries(self):
        endpoint = self.endpoints.get('user-services-details')
        industry = Industry.objects.create(name='Industry')
        industry2 = Industry.objects.create(name='Industry2')
        data = {
            'years_of_experience': 'less_1_year',
            'bar_council': 'text',
            'followers': 100,
            'industries': [],
            'services': [],
            'generate_business': False,
            'professional_service_provider': False
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertDictEqual(data, resp.json())

    def test_user_services_update_success_without_services(self):
        endpoint = self.endpoints.get('user-services-details')
        services = services_models.UserServiceInfo.objects.create(
            user=self.user
        )
        industry = Industry.objects.create(name='Industry')
        industry2 = Industry.objects.create(name='Industry2')
        data = {
            'years_of_experience': 'less_1_year',
            'bar_council': 'text',
            'followers': 100,
            'industries': [industry.pk, industry2.pk],
            'professional_service_provider': True,
            'generate_business': True,
            'services': [],
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertDictEqual(data, resp.json())
        services.refresh_from_db()
        self.assertEqual(services.years_of_experience, 'less_1_year')
        self.assertEqual(services.bar_council, 'text')
        self.assertEqual(services.followers, 100)
        self.assertIn(industry, services.industries.all())
        self.assertIn(industry2, services.industries.all())
        self.assertTrue(services.professional_service_provider)
        self.assertTrue(services.generate_business)

    def test_user_investor_services_get_fail_unauth(self):
        endpoint = self.endpoints.get('user-investor-details')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_user_investor_services_get_fail_no_data(self):
        endpoint = self.endpoints.get('user-investor-details')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(404, resp.status_code)

    def test_user_investor_services_get_fail_wrong_role(self):
        endpoint = self.endpoints.get('user-investor-details')
        services = services_models.UserServiceInfo.objects.create(
            user=self.user
        )
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(404, resp.status_code)

    def test_user_investor_services_get_success(self):
        endpoint = self.endpoints.get('user-investor-details')
        services = services_models.InvestorServiceInfo.objects.create(
            user=self.user,
            attachments=[],
            questions=[]
        )
        self.user.groups.clear()
        g = auth_models.Group.objects.get(name='Investor')
        self.user.groups.add(g)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)

    def test_investor_services_set(self):
        endpoint = self.endpoints.get('user-investor-details')
        services = services_models.InvestorServiceInfo.objects.create(
            user=self.user,
            attachments=[],
            questions=[]
        )
        self.user.groups.clear()
        g = auth_models.Group.objects.get(name='Investor')
        self.user.groups.add(g)
        funding = Funding.objects.create(name='Funding')
        company = Company.objects.create(name='Company')
        data = {
            'years_of_experience': 'less_1_year',
            'number_of_startups': 100,
            'kind_of_funding': [funding.pk],
            'companies': [company.pk],
            'connect_with_us': True,
            'process': 'Text',
            'attachments': ['First attach', 'Second attach'],
            'questions': ['First question', 'Second question'],
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(200, resp.status_code)

    def test_investor_services_set_2(self):
        endpoint = self.endpoints.get('user-investor-details')
        self.user.groups.clear()
        g = auth_models.Group.objects.get(name='Investor')
        self.user.groups.add(g)
        funding = Funding.objects.create(name='Funding')
        company = Company.objects.create(name='Company')
        data = {
            'years_of_experience': 'less_1_year',
            'number_of_startups': 100,
            'kind_of_funding': [funding.pk],
            'companies': [company.pk],
            'connect_with_us': True,
            'understand': True,
            'reach_out': True,
            'process': 'Text',
            'attachments': ['First attach', 'Second attach'],
            'questions': ['First question', 'Second question'],
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(200, resp.status_code)

    def test_investor_services_set_3(self):
        endpoint = self.endpoints.get('user-investor-details')
        self.user.groups.clear()
        g = auth_models.Group.objects.get(name='Investor')
        self.user.groups.add(g)
        funding = Funding.objects.create(name='Funding')
        company = Company.objects.create(name='Company')
        data = {
            'understand': True,
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_services)

    def test_investor_services_set_4(self):
        endpoint = self.endpoints.get('user-investor-details')
        self.user.groups.clear()
        g = auth_models.Group.objects.get(name='Investor')
        self.user.groups.add(g)
        funding = Funding.objects.create(name='Funding')
        company = Company.objects.create(name='Company')
        data = {
            'understand': True,
            'reach_out': True
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(400, resp.status_code)

    def test_user_services_set_with_services(self):
        endpoint = self.endpoints.get('user-services-details')
        services = services_models.UserServiceInfo.objects.create(
            user=self.user
        )
        category = services_models.Category.objects.create(
            name='Test'
        )
        service_type = services_models.ServiceType.objects.create(
            category=category,
            name='Type',
            description='Description',
            group='service'
        )
        industry = Industry.objects.create(name='Industry')
        industry2 = Industry.objects.create(name='Industry2')
        data = {
            'years_of_experience': 'less_1_year',
            'bar_council': 'text',
            'followers': 100,
            'industries': [industry.pk, industry2.pk],
            'services': [
                {
                    'pk': 1,
                    'service_type': service_type.pk,
                    'price_type': 'price',
                    'price': 100,
                    'timeline': 60,
                    'revision': 5,
                    'includes': 'test',
                    'attachments': ['1', '2'],
                    'questions': ['1', '2']

                },
                {
                    'service_type': service_type.pk,
                    'price_type': 'price',
                    'price': 100,
                    'timeline': 60,
                    'revision': 5,
                    'includes': 'test',
                    'attachments': ['1', '2'],
                    'questions': ['1', '2']

                }
            ],
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, len(resp.json()['services']))


    def test_user_services_set_with_services_2(self):
        endpoint = self.endpoints.get('user-services-details')
        services = services_models.UserServiceInfo.objects.create(
            user=self.user
        )
        category = services_models.Category.objects.create(
            name='Test'
        )
        service_type = services_models.ServiceType.objects.create(
            category=category,
            name='Type',
            description='Description',
            group='service'
        )
        industry = Industry.objects.create(name='Industry')
        industry2 = Industry.objects.create(name='Industry2')
        data = {
            'years_of_experience': 'less_1_year',
            'bar_council': 'text',
            'followers': 100,
            'industries': [industry.pk, industry2.pk],
            'services': [
                {
                    'pk': 1,
                    'service_type': service_type.pk,
                    'price_type': 'price',
                    'price': 100,
                    'timeline': 60,
                    'revision': 5,
                    'includes': 'test',
                    'attachments': [],
                    'questions': []

                },
                {
                    'service_type': service_type.pk,
                    'price_type': 'price',
                    'price': 100,
                    'timeline': 60,
                    'revision': 5,
                    'includes': 'test',
                    'attachments': [],
                    'questions': []

                }
            ],
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(2, len(resp.json()['services']))

    def test_user_services_set_minumum_info(self):
        endpoint = self.endpoints.get('user-services-details')

        data = {
            'professional_service_provider': False,
            'generate_business': False
        }
        resp = self.auth_client.post(endpoint, data, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_services)


class RefererTestCase(TestCase):
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
            'refer': reverse('v1:users:referer'),
            'register': reverse('v1:users:rest_register'),
        }

        self.country = locations_models.Country.objects.create(name='Country')
        self.city = CityProxy.objects.create(name='City', country=self.country)
        self.tag = Tag.objects.create(name='Tag')

    def test_refer_friend_authentication_required(self):
        response = self.client.post(self.endpoints['refer'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('users.views.send_email.delay', return_value=None)
    def test_send_invitation_email(self, send_email):
        response = self.auth_client.post(self.endpoints['refer'], data={'email': 'test@gmail.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_email.assert_called_once()

    @mock.patch('users.views.send_email.delay', return_value=None)
    def test_send_invitation_email_not_valid(self, send_email):
        response = self.auth_client.post(self.endpoints['refer'], data={'email': 'WRONG.com'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        send_email.assert_not_called()

    @mock.patch('users.models.User.send_verify_email', return_value=None)
    def test_success_register(self, send_email):
        endpoint = self.endpoints.get('register')
        uuid = str(self.user.pk)
        fernet = Fernet(settings.FERNET_KEY)
        encrypted_uuid = fernet.encrypt(uuid.encode('ascii')).decode("ascii")
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': 'Testy User', 'referer': encrypted_uuid}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        user = models.User.objects.get(email='test1@email.com')
        self.assertEqual(user.referer.email, 'test@email.com')


class InvestorTestCase(TestCase):
    def setUp(self):
        self.country = locations_models.Country.objects.create(name='Country')
        self.city = CityProxy.objects.create(name='City', country=self.country)
        self.work_city = WorkCityProxy.objects.create(name='WorkCity', country=self.country)
        self.work_city2 = WorkCityProxy.objects.create(name='WorkCity2', country=self.country)
        self.tag = Tag.objects.create(name='Tag')
        group = auth_models.Group.objects.get(name='Investor')
        self.fund1 = Funding.objects.create(name='Fund')
        self.fund2 = Funding.objects.create(name='Fund2')
        self.company = Company.objects.create(name='Company')
        self.company2 = Company.objects.create(name='Company2')
        for i in range(1, 21):
            user = models.User.objects.create(
                email=f'test{i}@email.com',
                name='ftest ltest',
                city=self.city,
            )
            models.Profile.objects.create(
                user=user,
                name='Testy',
                work_city=self.work_city if i <= 5 else self.work_city2
            )
            s = services_models.InvestorServiceInfo.objects.create(
                user=user,
                attachments=[],
                questions=[],
                reach_out=True
            )
            if i > 10:
                s.kind_of_funding.add(self.fund1)
                s.companies.add(self.company)
                if i > 15:
                    s.kind_of_funding.add(self.fund2)
                    s.companies.add(self.company2)
            BankDetails.objects.create(
                user=user,
                membership='basic',
                terms_and_condition=True
            )
            user.groups.add(group)
            user.save()
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
            'investor': reverse('v1:users:investors-list'),
        }

    def test_get_fail_unauth(self):
        endpoint = self.endpoints.get('investor')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(401, resp.status_code)

    def test_get_success(self):
        endpoint = self.endpoints.get('investor')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(20, len(resp.json()['results']))

    def test_get_success_with_custom_pagination(self):
        endpoint = self.endpoints.get('investor')
        resp = self.auth_client.get(f'{endpoint}?page_size=5', content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(5, len(resp.json()['results']))

    def test_get_success_with_fund_filter(self):
        endpoint = self.endpoints.get('investor')
        resp = self.auth_client.get(
            f'{endpoint}?investor_services_info__kind_of_funding={self.fund1.pk}&investor_services_info__kind_of_funding={self.fund2.pk}',
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(10, len(resp.json()['results']))

    def test_get_success_with_company_filter(self):
        endpoint = self.endpoints.get('investor')
        resp = self.auth_client.get(
            f'{endpoint}?investor_services_info__companies={self.company.pk}&investor_services_info__companies={self.company2.pk}',
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(10, len(resp.json()['results']))

    def test_get_success_with_work_city_filter(self):
        endpoint = self.endpoints.get('investor')
        resp = self.auth_client.get(
            f'{endpoint}?profile__work_city={self.work_city2.pk}',
            content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(15, len(resp.json()['results']))

