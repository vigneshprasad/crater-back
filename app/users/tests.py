from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_auth.utils import jwt_encode

from locations import models as locations_models
from tags.models import Tag
from users import models
from utils.file_test_service import get_test_base64_image


class AuthTestCase(TestCase):
    def setUp(self):
        self.user = models.User.objects.create(
            email='test@email.com',
            name='ftest ltest'
        )
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
            'user-profile': reverse('v1:users:profile-list')
        }

        self.country = locations_models.Country.objects.create(name='Country')
        self.city = locations_models.City.objects.create(name='City', country=self.country)
        self.tag = Tag.objects.create(name='Tag')

    def test_login_success(self):
        endpoint = self.endpoints.get('login')
        data = {'email': 'test@email.com', 'password': 'Qwer1234!'}
        resp = self.client.post(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json())

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

    def test_success_register(self):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': 'Testy User'}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(data.get('name'), resp.json()['user']['name'])
        self.assertEqual(data.get('email'), resp.json()['user']['email'])
        self.assertIn('token', resp.json())

    def test_fail_register_empty_name(self):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': ''}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('name', resp.json())
        self.assertEqual(['Please enter your name'], resp.json()['name'])

    def test_fail_register_name_too_long(self):
        endpoint = self.endpoints.get('register')
        data = {'email': 'test1@email.com', 'password': 'Qwer1234!', 'name': 'name'*40}
        resp = self.client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('name', resp.json())
        self.assertEqual(['Please enter the valid name'], resp.json()['name'])

    def test_regiter_success_email_with_camelcase(self):
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

    def test_reason_user_change_fail(self):
        endpoint = self.endpoints.get('user-details')
        data = {
            'reason': '123123'
        }
        resp = self.auth_client.patch(endpoint, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('reason', resp.json())

    def test_has_profile(self):
        self.assertFalse(self.user.has_profile)
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
            'name': self.user.name,
            'reason': None,
            'city': None,
            'full_registered': False,
            'has_profile': False
        }
        self.assertDictEqual(data, resp.json())

    def test_profile_get_fail_unauth(self):
        endpoint = self.endpoints.get('user-profile')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_profile_get_fail_not_found(self):
        endpoint = self.endpoints.get('user-profile')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 404)

    def test_profile_get_success(self):
        city = locations_models.City.objects.create(name='Work City', is_work=True, country=self.country)
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=city
        )
        endpoint = self.endpoints.get('user-profile')
        data = {
            'name': 'Testy',
            'tags': [],
            'tag_line': '',
            'cover': None,
            'photo': None,
            'introduction': '',
            'focus': '',
            'instagram': '',
            'twitter': '',
            'additional_information': '',
            'work_city': city.pk,
            'public_profile': True
        }
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(data, resp.json())

    def test_profile_set_success(self):
        endpoint = self.endpoints.get('user-profile')
        city = locations_models.City.objects.create(name='Work City', is_work=True, country=self.country)
        data = {
            'name': 'Test',
            'tags': [self.tag.pk],
            'tag_line': '',
            'cover': None,
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

    def test_profile_set_success_full_info(self):
        endpoint = self.endpoints.get('user-profile')
        city = locations_models.City.objects.create(name='Work City', is_work=True, country=self.country)
        data = {
            'name': 'Test',
            'tags': [self.tag.pk],
            'tag_line': '',
            'photo': None,
            'cover': None,
            'introduction': 'Introduction',
            'focus': 'Focus',
            'additional_information': 'Information',
            'work_city': city.pk,
            'instagram': 'https://instagram.com/',
            'twitter': 'https://twitter.com/',
            'public_profile': True
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_profile)
        self.assertDictEqual(data, resp.json())

    def test_profile_change_success(self):
        endpoint = self.endpoints.get('user-profile')
        models.Profile.objects.create(
            user=self.user,
            name='Testy'
        )
        city = locations_models.City.objects.create(name='Work City', is_work=True, country=self.country)
        data = {
            'name': 'Test',
            'introduction': 'Introduction',
            'focus': 'Focus',
            'additional_information': 'Additional Information',
            'work_city': city.pk,
            'tags': [self.tag.pk],
            'photo': get_test_base64_image(),
            'cover': get_test_base64_image()
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
