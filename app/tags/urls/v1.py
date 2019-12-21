from django.urls import path, include
from rest_framework import routers

from tags import views
from tags.views import WebsiteViewSet

app_name = 'tags'

router = routers.SimpleRouter()
router.register('user', views.TagViewSet)
router.register('masterclasses', views.MasterClassViewSet)
router.register('articles', views.ArticleTagViewSet)
router.register('websites', WebsiteViewSet)


urlpatterns = [
    path('', include(router.urls))
]
