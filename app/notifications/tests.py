from django.contrib.auth import models as auth_models
from django.test import TestCase, Client
from django.urls import reverse
from rest_auth.utils import jwt_encode

from community.comments.models import Comment
from community.groups.models import Location, Group, UserRequest
from community.posts.models import Post
from locations.models import Country, City
from resources.curated_articles.models import CuratedArticle
from resources.events.models import Event
from resources.masterclasses.models import MasterClass
from tags.models import WorkCityProxy, SourceWebsite, ArticleTag
from users import models


class NotificationSettingsTestCase(TestCase):
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
            'settings': reverse('v1:notifications:user-settings-list')
        }

    def test_set_up_success(self):
        self.assertEqual(1, 1)

    def test_get_settings_fail_unauth(self):
        endpoint = self.endpoints.get('settings')
        resp = self.client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_get_settings_success(self):
        endpoint = self.endpoints.get('settings')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        for value in resp.json().values():
            self.assertTrue(value)

    def test_change_settings_success(self):
        endpoint = self.endpoints.get('settings')
        data = {
            'messages': False,
            'post_comments': False,
            'post_likes': False,
            'new_videos_posted': False,
            'new_articles_posted': False,
            'new_events_created': False,
            'new_post_created': False,
        }
        resp = self.auth_client.post(endpoint, data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        get_resp = self.auth_client.get(endpoint, content_type='application/json')
        for value in get_resp.json().values():
            self.assertFalse(value)


class NotificationTestCase(TestCase):
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
            'my-list': reverse('v1:notifications:my-list'),
            'my-detail': lambda x: reverse('v1:notifications:my-detail', kwargs={'pk': x}),
            'my-read': lambda x: reverse('v1:notifications:my-read', kwargs={'pk': x}),
        }
        self.user2 = models.User.objects.create(
            email='test2@email.com',
            name='ftest ltest'
        )
        group = auth_models.Group.objects.get(name='User')
        self.user2.groups.add(group)
        self.user2.set_password('Qwer1234!')
        self.user2.save()
        self.token2 = jwt_encode(self.user2)
        self.auth_client2 = Client(HTTP_AUTHORIZATION=f'JWT {self.token2}')
        self.test_country = Country.objects.create(name='Test country')
        self.test_city = City.objects.create(name='Test city', country=self.test_country)
        self.test_work_city = WorkCityProxy.objects.create(name='Test city', country=self.test_country)
        self.user3 = models.User.objects.create(
            email='test3@email.com',
            name='ftest ltest'
        )
        models.Profile.objects.create(
            user=self.user3,
            name='Testy',
            work_city=self.test_work_city,
            introduction='Introduction'
        )
        models.Profile.objects.create(
            user=self.user,
            name='Testy',
            work_city=self.test_work_city,
            introduction='Introduction'
        )
        models.Profile.objects.create(
            user=self.user2,
            name='Testy',
            work_city=self.test_work_city,
            introduction='Introduction'
        )
        self.tag1 = ArticleTag.objects.create(name='Tag 1')
        self.community_location = Location.objects.create(name='Test location')
        self.community_group = Group.objects.create(location=self.community_location, name='Group name')
        UserRequest.objects.create(user=self.user, group=self.community_group, is_approved=True)
        UserRequest.objects.create(user=self.user2, group=self.community_group, is_approved=True)

    def test_set_up(self):
        self.assertEqual(1, 1)

    def test_event_created(self):
        Event.objects.create(
            title='Test title',
            text='Test text',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        self.assertTrue(self.user.notifications.filter(is_read=False).exists())
        self.assertTrue(self.user2.notifications.filter(is_read=False).exists())
        endpoint = self.endpoints.get('my-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(1, len(resp.json()['results']))

    def test_article_created(self):
        website = SourceWebsite.objects.create(name='Website 1', url='http://test.com')
        CuratedArticle.objects.create(title='Article 1', text='Text 1', tag=self.tag1, website_tag=website)
        self.assertTrue(self.user.notifications.filter(is_read=False).exists())
        self.assertTrue(self.user2.notifications.filter(is_read=False).exists())
        endpoint = self.endpoints.get('my-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(1, len(resp.json()['results']))

    def test_master_class_created(self):
        MasterClass.objects.create(
            author='Teacher 1',
            position='Position 1',
            description='Test description1'
        )
        self.assertTrue(self.user.notifications.filter(is_read=False).exists())
        self.assertTrue(self.user2.notifications.filter(is_read=False).exists())
        endpoint = self.endpoints.get('my-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(1, len(resp.json()['results']))

    def test_post_created(self):
        Post.objects.create(message='Test message old', creator=self.user)
        self.assertFalse(self.user.notifications.filter(is_read=False).exists())
        self.assertTrue(self.user2.notifications.filter(is_read=False).exists())
        endpoint = self.endpoints.get('my-list')
        resp = self.auth_client2.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_post_group_created(self):
        Post.objects.create(message='Test message old', creator=self.user2, group=self.community_group)
        self.assertFalse(self.user2.notifications.filter(is_read=False).exists())
        self.assertFalse(self.user3.notifications.filter(is_read=False).exists())
        self.assertTrue(self.user.notifications.filter(is_read=False).exists())
        endpoint = self.endpoints.get('my-list')
        resp = self.auth_client.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_comment_created(self):
        post = Post.objects.create(message='Test message old', creator=self.user)
        Comment.objects.create(post=post, message='Message', creator=self.user2)
        self.assertTrue(self.user.notifications.filter(is_read=False).exists())
        self.assertTrue(self.user.notifications.filter(is_read=False, notification__comment__isnull=False).exists())
        endpoint = self.endpoints.get('my-list')
        resp = self.auth_client2.get(endpoint, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(resp.json()['results']))

    def test_comment_mark_read(self):
        post = Post.objects.create(message='Test message old', creator=self.user)
        Comment.objects.create(post=post, message='Message', creator=self.user2)
        pk = self.user2.notifications.filter(is_read=False).first().pk
        endpoint = self.endpoints.get('my-read')(pk)
        resp = self.auth_client2.post(endpoint, {}, content_type='application/json')
        self.assertEqual(200, resp.status_code)
        self.assertTrue(self.user2.notifications.filter(is_read=True).exists())
