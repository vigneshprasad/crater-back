from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from tags.models import Industry, Company, Funding
from users.models import User
from users.serializers import ProfileSerializer
from . import models


class ServiceTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ServiceType
        fields = (
            'pk',
            'name',
            'description',
            'group'
        )


class CategorySerializer(serializers.ModelSerializer):
    service_types = ServiceTypeSerializer(many=True)

    class Meta:
        model = models.Category
        fields = ('pk', 'name', 'service_types', 'photo')


class ServiceSerializer(serializers.ModelSerializer):
    service_type_name = serializers.CharField(source='service_type.name', read_only=True)
    service_group = serializers.CharField(source='service_type.group', read_only=True)
    service_group_display = serializers.CharField(source='service_type.get_group_display', read_only=True)
    service_type_description = serializers.CharField(source='service_type.description', read_only=True)
    pk = serializers.IntegerField(required=False)

    class Meta:
        model = models.Service
        fields = (
            'pk',
            'status',
            'service_type',
            'service_group',
            'service_group_display',
            'service_type_name',
            'service_type_description',
            'price_type',
            'price',
            'timeline',
            'revision',
            'includes',
            'attachments',
            'questions',
            'rating'
        )
        read_only_fields = (
            'status',
            'rating',
            'service_type_name',
            'service_group',
            'service_group_display',
            'service_type_description'
        )


class UserServicesSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, required=False)
    industries = serializers.PrimaryKeyRelatedField(
        allow_empty=True, required=False, many=True, queryset=Industry.objects.all()
    )

    class Meta:
        model = models.UserServiceInfo
        fields = [
            'years_of_experience',
            'bar_council',
            'followers',
            'industries',
            'services',
            'professional_service_provider',
            'generate_business'
        ]

    def create(self, validated_data):
        services = validated_data.pop('services') if 'services' in validated_data else None
        instance = super().create(validated_data)
        if services:
            self.update_services(instance, services)
        return instance

    def update(self, instance, validated_data):
        services = validated_data.pop('services') if 'services' in validated_data else None
        instance = super().update(instance, validated_data)
        if services:
            self.update_services(instance, services)
        return instance

    @staticmethod
    def update_services(instance, services):
        instance.services.clear()
        for service in services:
            service_instance = None
            if 'pk' in service:
                pk = service.pop('pk')
                try:
                    service_instance = models.Service.objects.filter(pk=pk)
                    if service_instance.exists() and service_instance[0].user == instance.user:
                        if service['service_type'] == 'upon':
                            service['price'] = None
                        service_instance.update(**service)
                        service_instance = service_instance[0]
                    else:
                        service_instance = None
                except models.Service.DoesNotExist:
                    service_instance = models.Service.objects.create(
                        user=instance.user,
                        **service
                    )
            if not service_instance:
                service_instance = models.Service.objects.create(
                    user=instance.user,
                    **service
                )
            instance.services.add(service_instance)
        services = instance.services.filter(price_type='price', status='approved')
        instance.user.price_start = None
        if services.exists():
            instance.user.price_start = min(list(services.values_list('price', flat=True)))
        instance.user.save()


class InvestorServicesSerializer(serializers.ModelSerializer):
    kind_of_funding = serializers.PrimaryKeyRelatedField(many=True, queryset=Funding.objects.all(), required=False)
    companies = serializers.PrimaryKeyRelatedField(many=True, queryset=Company.objects.all(), required=False)

    class Meta:
        model = models.InvestorServiceInfo
        fields = [
            'years_of_experience',
            'number_of_startups',
            'kind_of_funding',
            'companies',
            'connect_with_us',
            'process',
            'attachments',
            'questions',
            'understand',
            'reach_out',
            'pk'
        ]

    def validate(self, attrs):
        reach_out = attrs.get('reach_out')
        if reach_out:
            errors = {}
            kind_of_funding = attrs.get('kind_of_funding')
            companies = attrs.get('companies')
            process = attrs.get('process')
            if not kind_of_funding:
                errors.update({'kind_of_funding': _('This field is required')})
            if not companies:
                errors.update({'companies': _('This field is required')})
            if not process:
                errors.update({'process': _('This field is required')})
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class ProfessionalServiceSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(source='user.profile')
    user_pk = serializers.IntegerField(source='user_id')

    class Meta:
        model = models.Service
        fields = (
            'pk',
            'profile',
            'user_pk',
            'rating',
            'rating_count',
            'price'
        )


class ProfessionalSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    followers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'pk',
            'profile',
            'rating',
            'rating_count',
            'price_start',
            'followers'
        )

    @staticmethod
    def get_followers(obj):
        if hasattr(obj, 'user_services_info') and obj.user_services_info:
            return obj.user_services_info.followers
        return None


class PublicUserServicesInfoSerializer(UserServicesSerializer):
    services = serializers.SerializerMethodField()

    class Meta:
        model = models.UserServiceInfo
        fields = [
            'pk',
            'years_of_experience',
            'bar_council',
            'followers',
            'industries',
            'services',
        ]

    def get_services(self, obj):
        ordering = None
        try:
            ordering = self.context['request'].query_params.get('ordering')
        except TypeError:
            pass
        services = obj.services.filter(status='approved')
        return ServiceSerializer(services.order_by(ordering) if ordering else services, many=True).data
