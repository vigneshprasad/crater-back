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
        if services:
            self.update_services(instance, services)
        return instance

    def update(self, instance, validated_data):
        services = validated_data.pop('services')
        instance = super().update(instance, validated_data)
        if services:
            self.update_services(instance, services)
        return instance

    def update_services(self, instance, services):
        instance.services.clear()
        print(len(services))
        for service in services:
            service_instance = None
            if 'pk' in service:
                pk = service.pop('pk')
                try:
                    service_instance = models.Service.objects.filter(pk=pk)
                    if service_instance.exists() and service_instance[0].user == instance.user:
                        service_instance.update(**service)
                        service_instance = service_instance[0]
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
        print(instance.services.all())


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
