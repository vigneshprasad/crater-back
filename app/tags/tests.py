from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode
from rest_framework import status
from rest_framework.test import APITestCase

from tags import models
from users import models as user_models


class CityTestCase(TestCase):
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
            'list': reverse('v1:tags:tag-list'),
            'detail': lambda x: reverse('v1:tags:tag-detail', kwargs={'pk': x})
        }
        self.tag = models.Tag.objects.create(name='Tag')

    def test_list_fail_unauth(self):
        endpoint = self.endpoints.get('list')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_tags_list_success(self):
        endpoint = self.endpoints.get('list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(1, len(resp.json()))
        self.assertEqual('Tag', resp.json()[0]['name'])

    def test_retrieve_success(self):
        endpoint = self.endpoints.get('detail')(self.tag.pk)
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual('Tag', resp.json()['name'])

    def test_retrieve_fail_unauth(self):
        endpoint = self.endpoints.get('detail')(self.tag.pk)
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)


class ArticleTagTestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            email='user@user.com',
            name='user',
            username='User',
            is_superuser=False,
            is_active=True,
            is_staff=True,
            password=make_password('123qaz123!A')
        )

    def test_tags_authentication_required(self):
        url = reverse('v1:tags:articletag-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_article_tags(self):
        models.ArticleTag.objects.create(name='Tag 1')
        models.ArticleTag.objects.create(name='Tag 2')
        models.ArticleTag.objects.create(name='Tag 3')
        url = reverse('v1:tags:articletag-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['name'], 'Tag 1')
        self.assertEqual(response.data[1]['name'], 'Tag 2')
        self.assertEqual(response.data[2]['name'], 'Tag 3')


class MasterClassTagTestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            email='user@user.com',
            name='user',
            username='User',
            is_superuser=False,
            is_active=True,
            is_staff=True,
            password=make_password('123qaz123!A')
        )

    def test_tags_authentication_required(self):
        url = reverse('v1:tags:masterclasstag-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_masterclass_tags(self):
        models.MasterClassTag.objects.create(name='Tag 1')
        models.MasterClassTag.objects.create(name='Tag 2')
        models.MasterClassTag.objects.create(name='Tag 3')
        url = reverse('v1:tags:masterclasstag-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['name'], 'Tag 1')
        self.assertEqual(response.data[1]['name'], 'Tag 2')
        self.assertEqual(response.data[2]['name'], 'Tag 3')

