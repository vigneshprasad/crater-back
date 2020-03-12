from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from community.groups.models import Location, Group, UserRequest


class TestLocationView(APITestCase):
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
        self.community_location = Location.objects.create(name='Test location')
        self.community_group = Group.objects.create(location=self.community_location, name='Group name')

    def test_get_location_authentication_required(self):
        url = reverse('v1:community:location-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_location_authentication_success(self):
        url = reverse('v1:community:location-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'Test location')
        self.assertEqual(response.data[0]['groups'][0]['name'], 'Group name')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data[0]['groups']), 1)

    def test_get_my_groups_empty(self):
        url = reverse('v1:community:location-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}my/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_my_groups(self):
        url = reverse('v1:community:location-list')
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=True)
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}my/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Group name')

    def test_get_my_groups_not_approved(self):
        url = reverse('v1:community:location-list')
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=False)
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}my/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class TestUserRequestView(APITestCase):
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
        self.community_location = Location.objects.create(name='Test location')
        self.community_group = Group.objects.create(location=self.community_location, name='Group name')

    def test_get_location_authentication_required(self):
        url = reverse('v1:community:location-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_connect_to_group_request(self):
        url = reverse('v1:community:location-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, format='json', data={'group': self.community_group.id})
        user_group = UserRequest.objects.get(user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(user_group.is_approved)


class TestBlockView(APITestCase):
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
        self.abuser = get_user_model().objects.create(
            email='abuser@abuser.com',
            name='abuser',
            username='Abuser',
            is_superuser=False,
            is_active=True,
            is_staff=True,
            password=make_password('123qaz123!A')
        )
        self.community_location = Location.objects.create(name='Test location')
        self.community_group = Group.objects.create(location=self.community_location, name='Group name')

    def test_blocking_authentication_required(self):
        url = reverse('v1:community:block-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_block_user(self):
        url = reverse('v1:community:block-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, data={'blocked': self.abuser.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unblock_user(self):
        url = reverse('v1:community:block-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, data={'blocked': self.abuser.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url_detail = reverse('v1:community:block-detail', args=(self.abuser.pk,))
        response = self.client.delete(url_detail, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestFollowView(APITestCase):
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
        self.followed = get_user_model().objects.create(
            email='abuser@abuser.com',
            name='abuser',
            username='Abuser',
            is_superuser=False,
            is_active=True,
            is_staff=True,
            password=make_password('123qaz123!A')
        )
        self.community_location = Location.objects.create(name='Test location')
        self.community_group = Group.objects.create(location=self.community_location, name='Group name')

    def test_following_authentication_required(self):
        url = reverse('v1:community:following-list')
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_user(self):
        url = reverse('v1:community:following-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, data={'followed': self.followed.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unfollow_user(self):
        url = reverse('v1:community:following-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, data={'followed': self.followed.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url_detail = reverse('v1:community:following-detail', args=(self.followed.pk,))
        response = self.client.delete(url_detail, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
