from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from utils.fields import Base64FileField
from . import models


class ExchangeCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExchangeCategory
        fields = [
            'pk',
            'name'
        ]


class ExchangeRequestSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', allow_null=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    files_base64 = serializers.ListField(
        required=False, child=Base64FileField(
            max_length=None, file_formats=['.jpg', '.png', '.tiff', '.bmp'], use_url=True
        ), write_only=True
    )
    files = serializers.ListField(
        required=False, child=serializers.ImageField(
            max_length=None, use_url=True
        ), write_only=True
    )
    files_urls = serializers.SerializerMethodField()
    cover_image_base64 = Base64FileField(required=False)
    cover_image = serializers.ImageField(required=False)

    class Meta:
        model = models.ExchangeRequest
        fields = [
            'pk',
            'category',
            'category_name',
            'title',
            'city',
            'city_name',
            'user',
            'city_name',
            'days',
            'require',
            'cover_image',
            'cover_image_base64',
            'description',
            'special_requirement',
            'additional_information',
            'extended_price',
            'files',
            'files_base64',
            'files_urls'
        ]
        extra_kwargs = {
            'user': {'write_only': True},
        }

    def create(self, validated_data):
        files_json = validated_data.pop('files_base64', [])
        files = validated_data.pop('files', [])
        cover = validated_data.pop('cover_image_base64')
        if cover:
            validated_data['cover_image'] = cover
        obj = super().create(validated_data)
        self._create_post_files(files_json, files,  obj)
        return obj

    def get_files_urls(self, obj):
        return [self.context['request'].build_absolute_uri(file.image.url) for file in obj.files.all()]

    @staticmethod
    def _create_post_files(files_base64, files, obj):
        """
        Create post files for base64 data
        """
        if len(files) + len(files_base64) > 6:
            raise serializers.ValidationError({'files', _('Can\'t be attached more than 6 photos/videos')})
        for file in files:
            models.RequestImage.objects.create(request=obj, image=file)
        for file in files_base64:
            models.RequestImage.objects.create(request=obj, image=file)

    @staticmethod
    def validate(attrs):
        cover = attrs.get('cover_image')
        cover_base64 = attrs.get('cover_image_base64')
        if not (cover or cover_base64):
            raise serializers.ValidationError({'cover_image': _('This field is required')})
        return attrs
