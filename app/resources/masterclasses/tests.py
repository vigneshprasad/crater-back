from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from resources.masterclasses.models import MasterClass
from tags.models import MasterClassTag


class TestArticleView(APITestCase):
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

        self.tag1 = MasterClassTag.objects.create(name='Tag 1')
        self.tag2 = MasterClassTag.objects.create(name='Tag 2')
        self.tag3 = MasterClassTag.objects.create(name='Tag 3')

        m1 = MasterClass.objects.create(
            author='Teacher 1',
            position='Position 1',
            description='Test description1'
        )
        m1.tags.add(self.tag1)
        m1.tags.add(self.tag2)
        m2 = MasterClass.objects.create(
            author='Teacher 2',
            position='Position 2',
            description='Test description2'
        )
        m2.tags.add(self.tag1)
        m2.tags.add(self.tag2)
        m3 = MasterClass.objects.create(
            author='Teacher 3',
            position='Position 3',
            description='Test description3'
        )
        m3.tags.add(self.tag3)

    def test_masterclass_authentication_required(self):
        url = reverse('v1:resources:masterclass-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_masterclasses(self):
        url = reverse('v1:resources:masterclass-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['author'], 'Teacher 3')
        self.assertEqual(results[1]['author'], 'Teacher 2')
        self.assertEqual(results[2]['author'], 'Teacher 1')

        tags1 = results[0]['tags']
        self.assertEqual(len(tags1), 1)
        self.assertEqual(tags1[0]['name'], 'Tag 3')

        tags2 = results[1]['tags']
        self.assertEqual(len(tags2), 2)
        self.assertEqual(tags2[0]['name'], 'Tag 1')
        self.assertEqual(tags2[1]['name'], 'Tag 2')

        tags3 = results[2]['tags']
        self.assertEqual(len(tags3), 2)
        self.assertEqual(tags3[0]['name'], 'Tag 1')
        self.assertEqual(tags3[1]['name'], 'Tag 2')

    def test_get_all_masterclasses_filter_by_tag1(self):
        url = reverse('v1:resources:masterclass-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}?tags={self.tag1.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['author'], 'Teacher 2')
        self.assertEqual(results[1]['author'], 'Teacher 1')

        tags2 = results[0]['tags']
        self.assertEqual(len(tags2), 2)
        self.assertEqual(tags2[0]['name'], 'Tag 1')
        self.assertEqual(tags2[1]['name'], 'Tag 2')

        tags3 = results[1]['tags']
        self.assertEqual(len(tags3), 2)
        self.assertEqual(tags3[0]['name'], 'Tag 1')
        self.assertEqual(tags3[1]['name'], 'Tag 2')

    def test_get_all_masterclasses_filter_tag3(self):
        url = reverse('v1:resources:masterclass-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}?tags={self.tag3.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['author'], 'Teacher 3')

        tags1 = results[0]['tags']
        self.assertEqual(len(tags1), 1)
        self.assertEqual(tags1[0]['name'], 'Tag 3')

    def test_get_all_masterclasses_filter_all_tags(self):
        url = reverse('v1:resources:masterclass-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}?tags={self.tag3.pk},{self.tag2.pk},{self.tag1.pk}')
        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['author'], 'Teacher 3')
        self.assertEqual(results[1]['author'], 'Teacher 2')
        self.assertEqual(results[2]['author'], 'Teacher 1')

        tags1 = results[0]['tags']
        self.assertEqual(len(tags1), 1)
        self.assertEqual(tags1[0]['name'], 'Tag 3')

        tags2 = results[1]['tags']
        self.assertEqual(len(tags2), 2)
        self.assertEqual(tags2[0]['name'], 'Tag 1')
        self.assertEqual(tags2[1]['name'], 'Tag 2')

        tags3 = results[2]['tags']
        self.assertEqual(len(tags3), 2)
        self.assertEqual(tags3[0]['name'], 'Tag 1')
        self.assertEqual(tags3[1]['name'], 'Tag 2')
