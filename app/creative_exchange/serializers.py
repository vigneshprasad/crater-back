from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from order.models import Quote
from utils.fields import Base64FileField
from utils.utils import date_range
from . import models


class ExchangeCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExchangeCategory
        fields = [
            'pk',
            'name'
        ]


class HistoricalBidResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Quote
        fields = [
            'created',
            'price',
            'year_of_experience',
            'followers'
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
    cover_image_base64 = Base64FileField(required=False, write_only=True)
    cover_image = serializers.ImageField(required=False)
    user_name = serializers.SerializerMethodField()
    user_logo = serializers.SerializerMethodField()
    quotes_count = serializers.SerializerMethodField()

    class Meta:
        model = models.ExchangeRequest
        fields = [
            'pk',
            'category',
            'category_name',
            'title',
            'city',
            'city_name',
            'user_name',
            'user_logo',
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
            'files_urls',
            'created',
            'quotes_count'
        ]
        read_only_fields = [
            'created',
        ]

    def create(self, validated_data):
        files_json = validated_data.pop('files_base64', [])
        files = validated_data.pop('files', [])
        cover = validated_data.pop('cover_image_base64',None)
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
    def get_user_name(obj):
        if hasattr(obj, 'user') and obj.user:
            if hasattr(obj.user, 'profile') and obj.user.profile:
                return obj.user.profile.name
            return obj.user.name
        return ''

    def get_user_logo(self, obj):
        if hasattr(obj, 'user') and obj.user:
            if hasattr(obj.user, 'profile') and obj.user.profile and obj.user.profile.photo:
                try:
                    return self.context['request'].build_absolute_uri(obj.user.profile.photo.url)
                except AttributeError:
                    return None
        return None

    @staticmethod
    def get_quotes_count(obj):
        return obj.quotes.count()


class DetailExchangeRequestSerializer(ExchangeRequestSerializer):
    historical_bids = serializers.SerializerMethodField()
    graph_data = serializers.SerializerMethodField()

    class Meta:
        model = models.ExchangeRequest
        fields = [
            'pk',
            'category',
            'category_name',
            'title',
            'city',
            'city_name',
            'user_name',
            'user_logo',
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
            'files_urls',
            'created',
            'historical_bids',
            'graph_data',
            'quotes_count'

        ]
        read_only_fields = [
            'created',
            'historical_bids',
            'graph_data'
        ]

    @staticmethod
    def get_historical_bids(obj):
        quotes = Quote.objects.filter(exchange_request__category=obj.category)
        return HistoricalBidResponseSerializer(quotes[:5], many=True).data

    @staticmethod
    def get_graph_data(obj):
        six_month_ago = timezone.now() - timezone.timedelta(days=180)
        responses = Quote.objects.filter(exchange_request__category=obj.category, created__gte=six_month_ago)
        graph_data = {}
        day_average = 0
        for single_date in date_range(six_month_ago, timezone.now()):
            resps = responses.filter(created=single_date)
            if resps:
                day_average = round(sum(list(resps.values_list('price', flat=True))) / resps.count())
            graph_data[single_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')] = day_average
        half_year_avg = sum(graph_data.values())/len(graph_data.values())
        return {
            'half_year_avf': half_year_avg,
            'data': graph_data
        }


class ExchangeQuoteSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField(min_value=1, max_value=999999)
    timeline = serializers.IntegerField(min_value=1, max_value=99)
    revisions = serializers.IntegerField(min_value=1, max_value=10)
    year_of_experience =  serializers.IntegerField(min_value=1, max_value=50)
    includes = serializers.CharField(max_length=800, allow_blank=True)
    additional_text = serializers.CharField(max_length=800, allow_blank=True)
    require = serializers.CharField(max_length=800, allow_blank=True)
    exchange_request = serializers.PrimaryKeyRelatedField(queryset=models.ExchangeRequest.objects.all())

    class Meta:
        model = Quote
        fields = [
            'pk',
            'exchange_request',
            'price',
            'timeline',
            'revisions',
            'year_of_experience',
            'followers',
            'includes',
            'additional_text',
            'require',
        ]
