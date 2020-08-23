from rest_framework import mixins, viewsets
from rest_framework.response import Response

from services import serializers as service_serializers
from users import permissions
from users import models
from users.paginators import Pagination
from users.scripts.create_users_from_csv import create_user_and_profile


class TypeFormViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):

    def create(self, request, *args, **kwargs):
        form = request.data['form_response']
        fields = form['definition']['fields']
        answers = form['answers']
        user = {
            'email': form['hidden']['email'],
            'interests': [],
            'source': 'https://worknetwork.typeform.com/to/' + form['form_id']
        }

        for i in range(len(fields)):
            if fields[i]['ref'] == 'full_name':
                user['name'] = answers[i]['text']

            elif fields[i]['ref'] == 'phone_number':
                user['phone_number'] = answers[i]['phone_number']

            if fields[i]['ref'] == 'linkedin_url':
                user['linkedin_url'] = answers[i]['url']

            if fields[i]['ref'] == 'interests' and fields[i].get('allow_multiple_selections', False):
                for interest in answers[i]['choices']['labels']:
                    user['interests'].append(interest)
            elif fields[i]['ref'] == 'interests':
                user['interests'].append(answers[i]['choice']['label'])

        create_user_and_profile(
            full_name=user['name'],
            email=user['email'],
            phone_number=user['phone_number'],
            linkedin_url=user['linkedin_url'],
            interests=user['interests'],
            source=user['source']
        )

        return Response({'status': 'Success'})


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