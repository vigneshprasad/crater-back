from django.urls import path, include
from rest_framework import routers

from tags import views

app_name = 'tags'

router = routers.SimpleRouter()
router.register('user', views.TagViewSet)
router.register('masterclasses', views.MasterClassViewSet)
router.register('articles', views.ArticleTagViewSet)
router.register('websites', views.WebsiteViewSet)
router.register('industries', views.IndustryViewSet)
router.register('funding', views.FundingViewSet)
router.register('companies', views.CompanyViewSet)


urlpatterns = [
    path('', include(router.urls))
]
