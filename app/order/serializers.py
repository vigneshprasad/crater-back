from rest_framework import serializers

from services.serializers import ServiceSerializer
from utils.fields import Base64FileField
from . import models


class AnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Answer
        fields = [
            'question',
            'text'
        ]


class AttachmentSerializer(serializers.ModelSerializer):
    files_base64 = serializers.ListField(
        child=Base64FileField(),
        allow_empty=False,
        write_only=True
    )
    files_urls = serializers.SerializerMethodField()

    class Meta:
        model = models.Attachment
        fields = [
            'name',
            'files_base64',
            'files_urls'
        ]

    def get_files_urls(self, obj):
        return [self.context['request'].build_absolute_uri(file.file.url) for file in obj.files.all()]


class QuotePreferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.QuotePreference
        fields = [
            'date',
            'time_start',
            'time_end'
        ]

    def validate(self, attrs):
        time_start = attrs.get('time_start')
        time_end = attrs.get('time_end')
        if time_end < time_start:
            raise serializers.ValidationError(_('The start time cannot be later than the end time'))
        return attrs


class QuoteSerializer(serializers.ModelSerializer):
    buyer_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    service_data = ServiceSerializer(read_only=True, source='service')
    attachments = AttachmentSerializer(many=True)
    answers = AnswerSerializer(many=True)
    date_preferences = QuotePreferenceSerializer(many=True)

    class Meta:
        model = models.Quote
        fields = [
            'pk',
            'buyer',
            'buyer_name',
            'seller',
            'seller_name',
            'service',
            'service_data',
            'attachments',
            'answers',
            'date_preferences',
            'comment',
            'price',
            'timeline',
            'revisions',
            'note',
        ]
        read_only_fields = [
            'buyer',
            'price',
            'comment',
            'price',
            'timeline',
            'revisions',
            'note',
        ]

    @staticmethod
    def get_buyer_name(obj):
        if hasattr(obj.buyer, 'profile') and obj.buyer.profile:
            return obj.buyer.profile.name
        return obj.buyer.name

    @staticmethod
    def get_seller_name(obj):
        if hasattr(obj.seller, 'profile') and obj.seller.profile:
            return obj.seller.profile.name
        return obj.seller.name

    def create(self, validated_data):
        attachments = validated_data.pop('attachments')
        answers = validated_data.pop('answers')
        date_preferences = validated_data.pop('date_preferences')
        instance = super().create(validated_data)
        if attachments:
            self.update_attachments(instance, attachments)
        if answers:
            self.update_answers(instance, answers)
        if date_preferences:
            self.update_preferences(instance, date_preferences)
        return instance

    @staticmethod
    def update_attachments(instance, attachments):
        instance.attachments.all().delete()
        for attachment in attachments:
            attach = models.Attachment.objects.create(
                quote=instance,
                name=attachment['name']
            )
            for file in attachment['files_base64']:
                models.AttachmentFile.objects.create(
                    attachment=attach,
                    file=file
                )

    @staticmethod
    def update_answers(instance, answers):
        instance.answers.all().delete()
        for answer in answers:
            models.Answer.objects.create(
                quote=instance,
                question=answer['question'],
                text=answer['text']
            )

    @staticmethod
    def update_preferences(instance, preferences):
        instance.date_preferences.all().delete()
        for preference in preferences:
            models.QuotePreference.objects.create(
                quote=instance,
                date=preference['date'],
                time_start=preference['time_start'],
                time_end=preference['time_end']
            )


class FundingRequestSerializer(serializers.ModelSerializer):
    buyer_name = serializers.SerializerMethodField()
    investor_name = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True)
    answers = AnswerSerializer(many=True)

    class Meta:
        model = models.FundingRequest
        fields = [
            'pk',
            'investor',
            'investor_name',
            'buyer',
            'buyer_name',
            'attachments',
            'answers'
        ]
        read_only_fields = [
            'buyer'
        ]

    @staticmethod
    def get_buyer_name(obj):
        if hasattr(obj.buyer, 'profile') and obj.buyer.profile:
            return obj.buyer.profile.name
        return obj.buyer.name

    @staticmethod
    def get_investor_name(obj):
        if hasattr(obj.investor, 'profile') and obj.investor.profile:
            return obj.investor.profile.name
        return obj.investor.name

    def create(self, validated_data):
        attachments = validated_data.pop('attachments')
        answers = validated_data.pop('answers')
        instance = super().create(validated_data)
        if attachments:
            self.update_attachments(instance, attachments)
        if answers:
            self.update_answers(instance, answers)
        return instance

    @staticmethod
    def update_attachments(instance, attachments):
        instance.attachments.all().delete()
        for attachment in attachments:
            attach = models.Attachment.objects.create(
                funding_request=instance,
                name=attachment['name']
            )
            for file in attachment['files_base64']:
                models.AttachmentFile.objects.create(
                    attachment=attach,
                    file=file
                )

    @staticmethod
    def update_answers(instance, answers):
        instance.answers.all().delete()
        for answer in answers:
            models.Answer.objects.create(
                funding_request=instance,
                question=answer['question'],
                text=answer['text']
            )


class OrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.SerializerMethodField()
    buyer_photo = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    seller_photo = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    service_data = ServiceSerializer(read_only=True, source='service')
    attachments = AttachmentSerializer(many=True)
    answers = AnswerSerializer(many=True)

    class Meta:
        model = models.Order
        fields = [
            'pk',
            'created',
            'buyer',
            'buyer_name',
            'buyer_photo',
            'seller',
            'seller_name',
            'seller_photo',
            'service',
            'service_data',
            'price',
            'attachments',
            'answers',
            'note'
        ]
        read_only_fields = [
            'buyer'
        ]

    @staticmethod
    def get_buyer_name(obj):
        if hasattr(obj.buyer, 'profile') and obj.buyer.profile:
            return obj.buyer.profile.name
        return obj.buyer.name

    @staticmethod
    def get_seller_name(obj):
        if hasattr(obj.seller, 'profile') and obj.seller.profile:
            return obj.seller.profile.name
        return obj.seller.name

    def get_seller_photo(self, obj):
        if hasattr(obj.seller, 'profile') and obj.seller.profile and obj.seller.profile.photo:
            return self.context['request'].build_absolute_uri(obj.seller.profile.photo.url)
        return None

    def get_buyer_photo(self, obj):
        if hasattr(obj.buyer, 'profile') and obj.buyer.profile and obj.buyer.profile.photo:
            return self.context['request'].build_absolute_uri(obj.buyer.profile.photo.url)
        return None

    @staticmethod
    def get_price(obj):
        if obj.quote:
            price = obj.quote.service.price
        elif obj.creative_exchange_response:
            price = obj.creative_exchange_response.price
        else:
            price = obj.service.price
        return price

    def create(self, validated_data):
        attachments = validated_data.pop('attachments')
        answers = validated_data.pop('answers')
        instance = super().create(validated_data)
        if attachments:
            self.update_attachments(instance, attachments)
        if answers:
            self.update_answers(instance, answers)
        return instance

    @staticmethod
    def update_attachments(instance, attachments):
        instance.attachments.all().delete()
        for attachment in attachments:
            attach = models.Attachment.objects.create(
                order=instance,
                name=attachment['name']
            )
            for file in attachment['files_base64']:
                models.AttachmentFile.objects.create(
                    attachment=attach,
                    file=file
                )

    @staticmethod
    def update_answers(instance, answers):
        instance.answers.all().delete()
        for answer in answers:
            models.Answer.objects.create(
                order=instance,
                question=answer['question'],
                text=answer['text']
            )


class AcceptOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Order
        fields = [
            'note',
        ]


class ProvideQuoteSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField(max_value=999999, min_value=1)
    timeline = serializers.IntegerField(max_value=99, min_value=1)
    revisions = serializers.IntegerField(max_value=10, min_value=1)

    class Meta:
        modes = models.Quote
        fields = [
            'price',
            'comment',
            'price',
            'timeline',
            'revisions',
            'note',
        ]
