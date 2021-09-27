from rest_framework import viewsets, mixins
from django.db.models.functions import Lower
from rest_framework.response import Response
from . import models, serializers

from .serializers import ArticleTagSerializer, ArticleWebsiteSerializer
from .services import get_websites
from users import permissions
from rest_framework.decorators import action


class TagViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    queryset = models.Tag.objects.filter(is_active=True).order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = serializers.TagSerializer


class ObjectiveViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):                       
    queryset = models.Objective.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ObjectiveSerializer

    def get_queryset(self):
        if not self.request.user:
            return self.queryset
        return models.Objective.objects.filter(intent=self.request.user.intent)


class MasterClassViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = models.MasterClassTag.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.MasterClassTagSerializer


class ArticleTagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ArticleTagSerializer
    queryset = models.ArticleTag.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]


class CompanyViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Company.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.CompanySerializer


class FundingViewSet(mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    queryset = models.Funding.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingSerializer


class IndustryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = models.Industry.objects.all().order_by(Lower('name'))
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.IndustrySerializer


class WebsiteViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ArticleWebsiteSerializer
    queryset = get_websites()
    permission_classes = [permissions.IsAuthenticated]


class FaqViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.FaqSerializer
    queryset = models.Faq.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @action(
        methods=['GET'],
        detail=False,
    )
    def points(self, request):
        data = self.get_queryset().filter(category='points').order_by('order')
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid()
        return Response(serializer.data)