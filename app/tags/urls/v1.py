from django.urls import path, include
from rest_framework import routers

from tags import public_views
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
router.register('objectives', views.ObjectiveViewSet)
router.register('faq', views.FaqViewSet)

public_router = routers.SimpleRouter()
public_router.register('industries', public_views.IndustryViewSet)
public_router.register('funding', public_views.FundingViewSet)
public_router.register('companies', public_views.CompanyViewSet)

public_url_patterns = [
    path('', include(public_router.urls)),
]

urlpatterns = [
    path('', include(router.urls)),
    path('public/', include(public_url_patterns))
]
