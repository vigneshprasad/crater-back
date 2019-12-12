from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from community.posts.models import Post
from utils.file_test_service import get_test_base64_image, get_test_image


class TestPost(APITestCase):

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

    def test_post_creation_authentication_required(self):
        url = reverse('v1:community:post-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_creation_success_with_base64file(self):
        url = reverse('v1:community:post-list')
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.post(url, format='json', data={
                'message': 'Post message',
                'files_base64': [get_test_base64_image()]
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_creation_success_with_formdata(self):
        url = reverse('v1:community:post-list')
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.post(url, format='json', data={
                'message': 'Post message',
                'files': get_test_image()
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_posts_from_chat(self):
        url = reverse('v1:community:post-list')
        Post.objects.create(message='Test message', creator=self.user)
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['message'], 'Test message')
        self.assertEqual(response.data[0]['group'], None)
        self.assertEqual(response.data[0]['creator_name'], 'user')
        self.assertEqual(response.data[0]['likes'], 0)
        self.assertEqual(response.data[0]['comments'], 0)
        self.assertEqual(response.data[0]['latest_comments'], [])

    def test_get_post_from_chat(self):
        post = Post.objects.create(message='Test message', creator=self.user)
        url = reverse('v1:community:post-detail', args=(post.id,))
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Test message')
        self.assertEqual(response.data['group'], None)
        self.assertEqual(response.data['creator_name'], 'user')
        self.assertEqual(response.data['likes'], 0)
        self.assertEqual(response.data['comments'], 0)
        self.assertEqual(response.data['latest_comments'], [])

    def test_get_posts_from_closed_group(self):
        pass
        # Post.objects.create(message='Test message', creator=self.user)
        # url = reverse('v1:community:post-list')
        # self.client.login(email='user@user.com', password='123qaz123!A')
        # response = self.client.get(url, format='json')
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data['message'], 'Test message')
        # self.assertEqual(response.data['group'], None)
        # self.assertEqual(response.data['creator_name'], 'user')
        # self.assertEqual(response.data['likes'], 0)
        # self.assertEqual(response.data['comments'], 0)
        # self.assertEqual(response.data['latest_comments'], [])
