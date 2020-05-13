from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from community.comments.models import Comment
from locations.models import Country, City
from resources.events.models import Event, RSVPD


class TestEventView(APITestCase):
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
        self.test_country = Country.objects.create(name='Test country')
        self.test_city = City.objects.create(name='Test city', country=self.test_country)

    def test_events_authentication_required(self):
        url = reverse('v1:resources:event-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_empty_events(self):
        url = reverse('v1:resources:event-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_get_events(self):
        url = reverse('v1:resources:event-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
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

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(result['title'], 'Test title')

    def test_get_events_get_free_events_filter(self):
        url = reverse('v1:resources:event-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        Event.objects.create(
            title='Test title first',
            text='Test text first',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        Event.objects.create(
            title='Test title second',
            text='Test text second',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=False,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )

        response = self.client.get(f'{url}?is_free=true', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(result['title'], 'Test title first')
        self.assertEqual(result['text'], 'Test text first')

    def test_get_events_state_events_filter(self):
        url = reverse('v1:resources:event-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        Event.objects.create(
            title='Test title first',
            text='Test text first',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        Event.objects.create(
            title='Test title second',
            text='Test text second',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=False,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='past'
        )
        response = self.client.get(f'{url}?state=past', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(result['title'], 'Test title second')

    @mock.patch('resources.events.signals.send_email.delay')
    def test_get_events_rsvpd_events_filter(self, send_email):
        send_email.return_value = None
        url = reverse('v1:resources:event-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        event1 = Event.objects.create(
            title='Test title first',
            text='Test text first',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        event2 = Event.objects.create(
            title='Test title second',
            text='Test text second',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='past'
        )
        Event.objects.create(
            title='Test title third',
            text='Test text third',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=False,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        RSVPD.objects.create(event=event1, user=self.user)
        RSVPD.objects.create(event=event2, user=self.user)
        response = self.client.get(f'{url}?participated=true', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(result['title'], 'Test title first')

    def test_get_latest_comments(self):
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        event = Event.objects.create(
            title='Test title first',
            text='Test text first',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        Comment.objects.create(message='comment 1', event=event, creator=self.user)
        Comment.objects.create(message='comment 2', event=event, creator=self.user)
        Comment.objects.create(message='comment 3', event=event, creator=self.user)

        url = reverse('v1:resources:event-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(result['title'], 'Test title first')
        self.assertEqual(result['comments'], 3)
        self.assertEqual(len(result['latest_comments']), 2)
        self.assertEqual(result['latest_comments'][0]['message'], 'comment 3')
        self.assertEqual(result['latest_comments'][1]['message'], 'comment 2')

    def test_comment_creation_for_event(self):
        event = Event.objects.create(
            title='Test title first',
            text='Test text first',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        url = reverse('v1:community:comment-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, data={'message': 'Test comment creation', 'event': event.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('v1:resources:event-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(result['comments'], 1)
        self.assertEqual(len(result['latest_comments']), 1)
        self.assertEqual(result['latest_comments'][0]['message'], 'Test comment creation')

    def test_comment_list_for_event(self):
        event = Event.objects.create(
            title='Test title first',
            text='Test text first',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        Comment.objects.create(message='Test Message 1', creator=self.user, event=event)
        Comment.objects.create(message='Test Message 2', creator=self.user, event=event)
        Comment.objects.create(message='Test Message 3', creator=self.user, event=event)

        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))

        url = reverse('v1:resources:comment-list')
        response = self.client.get(f'{url}{event.pk}/event/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data['results'][0]
        self.assertEqual(result['message'], 'Test Message 1')

    @mock.patch('resources.events.signals.send_email.delay')
    def test_rsvpd_email_sent(self, email_sent):
        email_sent.return_value = None
        event = Event.objects.create(
            title='Test title first',
            text='Test text first',
            date='2001-01-01',
            start='11:20',
            end='12:00',
            is_free=True,
            is_rsvp_required=True,
            location=self.test_city,
            capacity=10,
            state='upcoming'
        )
        url = reverse('v1:resources:rsvpd-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.post(url, data={'event': event.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        email_sent.assert_called_once()
