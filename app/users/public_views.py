from rest_framework import mixins, viewsets
from rest_framework.response import Response
from resources.meetings import signals
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
            'email': form.get('hidden').get('email') if form.get('hidden') else None,
            'interests': [],
            'time_preferences': [],
            'meeting_days': [],
            'source': 'https://worknetwork.typeform.com/to/' + form['form_id']
        }

        for i in range(len(fields)):
            if fields[i]['ref'] == 'full_name':
                user['name'] = answers[i]['text']
            elif fields[i]['ref'] == 'email':
                user['email'] = answers[i]['email']
            elif fields[i]['ref'] == 'phone_number':
                user['phone_number'] = answers[i]['phone_number']
            elif fields[i]['ref'] == 'meeting_days':
                days = answers[i]['choice']['label']
                if days == 'Both work':
                    user['meeting_days'].append('Thursday')
                    user['meeting_days'].append('Friday')
                else:
                    user['meeting_days'].append(days)
            elif fields[i]['ref'] == 'linkedin_url':
                user['linkedin_url'] = answers[i]['url']
            elif fields[i]['ref'] == 'interests' and fields[i].get('allow_multiple_selections', False):
                for interest in answers[i]['choices']['labels']:
                    user['interests'].append(interest)
            elif fields[i]['ref'] == 'interests':
                user['interests'].append(answers[i]['choice']['label'])
            elif fields[i]['ref'] == 'time_preferences' and fields[i].get('allow_multiple_selections', False):
                for preference in answers[i]['choices']['labels']:
                    user['time_preferences'].append(preference)
            elif fields[i]['ref'] == 'time_preferences':
                user['time_preferences'].append(answers[i]['choice']['label'])

        if not user['email']:
            return Response({'status': 'No email exists'})
        else:
            user_obj, _ = create_user_and_profile(
                full_name=user['name'],
                email=user['email'],
                phone_number=user['phone_number'],
                linkedin_url=user['linkedin_url'],
                interests=user['interests'],
                source=user['source']
            )

            if not user['meeting_days']:
                user['meeting_days'] = ['Thursday', 'Friday']

            signals.create_new_meeting_preference_typeform.send(
                sender=None,
                user=user_obj,
                time_preferences=user['time_preferences'],
                interests=user['interests'],
                days=user['meeting_days']
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
