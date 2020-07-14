from rest_framework import mixins, viewsets, status

from services import serializers as service_serializers
from users import permissions
from . import models
from .paginators import Pagination


class InvestorsViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    queryset = models.User.objects.select_related('profile').filter(
        groups__name='Investor',
        # bank_details__isnull=False,
        investor_services_info__isnull=False,
        is_active=True,
        is_superuser=False,
        investor_services_info__reach_out=True,
        is_approved=True,
        profile__public_profile=True
    ).order_by('name')

    permission_classes = [permissions.AllowAny]
    pagination_class = Pagination
    # serializer_class = serializers.ProfileSerializer
    serializer_class = service_serializers.ProfessionalSerializer
    filterset_fields = [
        'investor_services_info__kind_of_funding',
        'investor_services_info__companies',
        'profile__work_city'
    ]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.User.objects.none()
        return self.queryset.exclude(pk=self.request.user.pk)
