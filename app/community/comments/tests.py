from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from community.comments.models import Comment
from community.groups.models import Location, Group
from community.posts.models import Post


class TestCommentView(APITestCase):
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

    def test_comments_authentication_required(self):
        url = reverse('v1:community:comment-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comments_creation(self):
        post = Post.objects.create(message='Test message', creator=self.user)
        url = reverse('v1:community:comment-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, data={'message': 'Test comment', 'post': post.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_comment_list(self):
        post = Post.objects.create(message='Test message', creator=self.user)
        post2 = Post.objects.create(message='Test message', creator=self.user)
        Comment.objects.create(message='Test message 1', post=post, creator=self.user)
        Comment.objects.create(message='Test message 2', post=post, creator=self.user)
        Comment.objects.create(message='Test message 3', post=post, creator=self.user)
        Comment.objects.create(message='Test message 4', post=post, creator=self.user)
        Comment.objects.create(message='Test message 5', post=post2, creator=self.user)
        url = reverse('v1:community:comment-detail', args=(post.id,))
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}post/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['message'], 'Test message 2')
        self.assertEqual(response.data['results'][1]['message'], 'Test message 1')
