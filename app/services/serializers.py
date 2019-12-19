from rest_framework import serializers

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
        fields = ('pk', 'name', 'service_types')


class ServiceSerializer(serializers.ModelSerializer):
    service_type_name = serializers.CharField(source='service_type.name')
    service_type_description = serializers.CharField(source='service_type.description')


    class Meta:
        model = models.Service
        fields = (
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

    class Meta:
        model = models.UserServiceInfo
        fields = [
            'years_of_experience',
            'bar_council',
            'followers',
            'industries',
            'services'
        ]

    def create(self, validated_data):
        services = validated_data.pop('services')
        instance = super().create(validated_data)
        self.update_services(instance, services)
        return instance

    def update(self, instance, validated_data):
        services = validated_data.pop('services')
        instance = super().update(instance, validated_data)
        self.update_services(instance, services)
        return instance

    def update_services(self, instance, validated_data):
        pass


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
        ]
