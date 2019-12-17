from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from community.groups.models import Location, Group, UserRequest
from community.posts.models import Post, Like, Report
from utils.file_test_service import get_test_base64_image, get_test_image


class TestPostView(APITestCase):

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
        Post.objects.create(message='Test message old', creator=self.user)
        Post.objects.create(message='Test message', creator=self.user)
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'][0]
        self.assertEqual(results['message'], 'Test message')
        self.assertEqual(results['group'], None)
        self.assertEqual(results['creator_name'], 'user')
        self.assertEqual(results['likes'], 0)
        self.assertEqual(results['comments'], 0)
        self.assertEqual(results['latest_comments'], [])

    def test_get_post_from_chat(self):
        url = reverse('v1:community:post-list')
        self.client.login(email='user@user.com', password='123qaz123!A')
        self.client.post(url, format='json', data={
            'message': 'Test message for community chat',
            'files_base64': [get_test_base64_image()]
        })
        post = Post.objects.get(message='Test message for community chat')
        url = reverse('v1:community:post-detail', args=(post.id,))
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Test message for community chat')
        self.assertEqual(response.data['group'], None)
        self.assertEqual(response.data['creator_name'], 'user')
        self.assertEqual(response.data['likes'], 0)
        self.assertEqual(response.data['comments'], 0)
        self.assertEqual(response.data['latest_comments'], [])
        self.assertIn('http://testserver/media/posts/freelance_file', response.data['files_urls'][0])

    def test_get_posts_from_closed_group_forbidden(self):
        Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        url = reverse('v1:community:post-detail', args=(self.community_group.id,))
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.get(f'{url}group/', format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_posts_from_group(self):
        Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=True)
        url = reverse('v1:community:post-detail', args=(self.community_group.id,))
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.get(f'{url}group/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_posts_from_group_not_approved_by_admin(self):
        Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=False)
        url = reverse('v1:community:post-detail', args=(self.community_group.id,))
        self.client.login(email='user@user.com', password='123qaz123!A')
        response = self.client.get(f'{url}group/', format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestLikeView(APITestCase):

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

    def test_like_creation_authentication_required(self):
        url = reverse('v1:community:like-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_post_create_like(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user)

        like_url = reverse('v1:community:like-list')
        response = self.client.post(like_url, data={'post': post.pk, 'user': self.user})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('v1:community:post-detail', args=(post.id,))
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Test message')
        self.assertEqual(response.data['group'], None)
        self.assertEqual(response.data['creator_name'], 'user')
        self.assertEqual(response.data['likes'], 1)
        self.assertEqual(response.data['comments'], 0)
        self.assertEqual(response.data['latest_comments'], [])

    def test_get_post_create_unlike(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user)

        like_url = reverse('v1:community:like-list')
        response = self.client.post(like_url, data={'post': post.pk, 'user': self.user})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        like_detail = reverse('v1:community:like-detail', args=(post.id,))
        response = self.client.delete(like_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        url = reverse('v1:community:post-detail', args=(post.id,))
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Test message')
        self.assertEqual(response.data['creator_name'], 'user')
        self.assertEqual(response.data['likes'], 0)
        self.assertEqual(response.data['comments'], 0)

    def test_get_post_create_like_forbidden_group(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user, group=self.community_group)

        like_url = reverse('v1:community:like-list')
        response = self.client.post(like_url, data={'post': post.pk, 'user': self.user})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_post_create_unlike_forbidden_group(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        Like.objects.create(post=post, user=self.user)

        like_detail = reverse('v1:community:like-detail', args=(post.id,))
        response = self.client.delete(like_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_like_in_allowed_group(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=True)
        like_url = reverse('v1:community:like-list')
        response = self.client.post(like_url, data={'post': post.pk})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_like_in_restricted_by_admin_group(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=False)
        like_url = reverse('v1:community:like-list')
        response = self.client.post(like_url, data={'post': post.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestReportView(APITestCase):

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

    def test_report_creation_authentication_required(self):
        url = reverse('v1:community:report-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_report(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user)

        report_url = reverse('v1:community:report-list')
        response = self.client.post(report_url, data={'post': post.pk})
        report = Report.objects.get(user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(report.is_reviewed)

    def test_create_report_forbidden_group(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user, group=self.community_group)

        report_url = reverse('v1:community:report-list')
        response = self.client.post(report_url, data={'post': post.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_report_in_allowed_group(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=True)

        report_url = reverse('v1:community:report-list')
        response = self.client.post(report_url, data={'post': post.pk})
        report = Report.objects.get(user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(report.is_reviewed)

    def test_create_report_in_group_not_approved_by_admin(self):
        self.client.login(email='user@user.com', password='123qaz123!A')
        post = Post.objects.create(message='Test message', creator=self.user, group=self.community_group)
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=False)

        report_url = reverse('v1:community:report-list')
        response = self.client.post(report_url, data={'post': post.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
