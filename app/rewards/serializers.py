from rest_framework import serializers

from rewards import models


class PackageProviderSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PackageProvider
        fields = (
            'name',
            'description',
            'logo',
        )


class PackageSerializer(serializers.ModelSerializer):
    provider = PackageProviderSerializer()

    class Meta:
        model = models.Package
        fields = (
            'pk',
            'max_price',
            'max_discount',
            'max_discount_points',
            'title',
            'short_desc',
            'list_image',
            'cover_image',
            'color',
            'provider',
            'long_desc',
            'points_conversion',
            'is_dark',
            'show_on_web',
        )


class PackageRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.PackageRequest
        fields = (
            'quantity',
            'requested_by',
            'package',
            'point_applied',
            'status',
        )
