from django.test import TestCase, Client
from django.urls import reverse
from users import models
from rest_auth.utils import jwt_encode


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
            'change-password': reverse('v1:users:rest_password_change')
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
