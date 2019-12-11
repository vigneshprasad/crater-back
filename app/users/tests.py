from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_auth.utils import jwt_encode

from users import models


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
            'user': reverse('v1:users:rest_user_details'),
            'register': reverse('v1:users:rest_register'),
            'change-password': reverse('v1:users:rest_password_change'),
            'reset-password': reverse('v1:users:rest_password_reset'),
            'reset-password-confirm': reverse('v1:users:rest_password_reset_confirm'),
            'user-details': reverse('v1:users:rest_user_details')
        }

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


