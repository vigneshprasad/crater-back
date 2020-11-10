from rest_framework import serializers

from rewards import models


class PackageSerializer(serializers.ModelSerializer):

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
