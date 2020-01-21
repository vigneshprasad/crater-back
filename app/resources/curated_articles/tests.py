from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from resources.curated_articles.models import CuratedArticle
from tags.models import ArticleTag, SourceWebsite


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

        self.tag1 = ArticleTag.objects.create(name='Tag 1')
        tag2 = ArticleTag.objects.create(name='Tag 2')
        self.tag3 = ArticleTag.objects.create(name='Tag 3')

        self.website = SourceWebsite.objects.create(name='Website 1', url='http://test.com')
        website = SourceWebsite.objects.create(name='Website 2', url='http://test.com')

        CuratedArticle.objects.create(title='Article 1', text='Text 1', tag=self.tag1, website_tag=self.website)
        CuratedArticle.objects.create(title='Article 2', text='Text 2', tag=self.tag1, website_tag=website)
        CuratedArticle.objects.create(title='Article 3', text='Text 3', tag=tag2, website_tag=self.website)
        CuratedArticle.objects.create(title='Article 4', text='Text 4', tag=self.tag3, website_tag=website)

    def test_article_authentication_required(self):
        url = reverse('v1:resources:curatedarticle-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_articles(self):
        url = reverse('v1:resources:curatedarticle-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]['title'], 'Article 4')
        self.assertEqual(results[1]['title'], 'Article 3')
        self.assertEqual(results[2]['title'], 'Article 2')
        self.assertEqual(results[3]['title'], 'Article 1')

    def test_get_articles_filtered_by_tag(self):
        url = reverse('v1:resources:curatedarticle-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}?tags={self.tag1.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Article 2')
        self.assertEqual(results[1]['title'], 'Article 1')

    def test_get_articles_filtered_by_website(self):
        url = reverse('v1:resources:curatedarticle-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        print(self.website.pk)
        response = self.client.get(f'{url}?website_tags={self.website.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Article 3')
        self.assertEqual(results[1]['title'], 'Article 1')

    def test_get_articles_filtered_by_website_and_tag(self):
        url = reverse('v1:resources:curatedarticle-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}?website_tags={self.website.pk}&tag={self.tag1.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Article 1')

    def test_get_articles_filtered_by_website_and_tag_empty_result(self):
        url = reverse('v1:resources:curatedarticle-list')
        response = self.client.post(
            reverse('v1:users:rest_login'), {'email': 'user@user.com', 'password': '123qaz123!A'}
        )
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='JWT {0}'.format(token))
        response = self.client.get(f'{url}?website_tags={self.website.pk}&tags={self.tag3.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 0)
