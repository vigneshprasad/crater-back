from rest_framework import serializers

from tags.models import Industry
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
    service_type_description = serializers.CharField(source='service_type.description', read_only=True)
    pk = serializers.IntegerField(required=False)

    class Meta:
        model = models.Service
        fields = (
            'pk',
            'status',
            'service_type',
            'service_type_name',
            'service_type_description',
            'price_type',
            'price',
            'timeline',
            'revision',
            'includes',
            'attachments',
            'questions'
        )
        read_only_fields = (
            'status',
            'service_type_name',
            'service_type_description'
        )


class UserServicesSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True)
    industries = serializers.PrimaryKeyRelatedField(allow_empty=True, many=True, queryset=Industry.objects.all())

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
        services = validated_data.pop('services')
        instance = super().create(validated_data)
        if services:
            self.update_services(instance, services)
        return instance

    def update(self, instance, validated_data):
        services = validated_data.pop('services')
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


class InvestorServicesSerializer(serializers.ModelSerializer):

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
    rating = serializers.SerializerMethodField()
    price_start = serializers.SerializerMethodField()
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
    def get_rating(obj):
        # TODO
        return 5.0

    def get_price_start(self, obj):
        price_from = self.context['request'].query_params.get('price_from')
        services = obj.services.filter(status='approved')
        if price_from:
            services = services.filter(price__gte=price_from)
        if services:
            return services.order_by('price')[0].price
        return None

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

    @staticmethod
    def get_services(obj):
        return ServiceSerializer(obj.services.filter(status='approved'), many=True).data
