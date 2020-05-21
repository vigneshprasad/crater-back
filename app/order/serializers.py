from django.utils.translation import ugettext_lazy as _
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
        try:
            return [
                {
                    'url': self.context['request'].build_absolute_uri(file.file.url),
                    'size': file.file.size
                }

                for file in obj.files.all()
            ]
        except:
            return []


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


class OrderPreferenceSerializer(QuotePreferenceSerializer):

    class Meta:
        model = models.OrderPreference
        fields = [
            'date',
            'time_start',
            'time_end'
        ]


class QuoteSerializer(serializers.ModelSerializer):
    buyer_name = serializers.SerializerMethodField()
    buyer_photo = serializers.FileField(source='buyer.profile.photo', allow_null=True, read_only=True)
    seller_name = serializers.SerializerMethodField()
    seller_photo = serializers.FileField(source='seller.profile.photo', allow_null=True, read_only=True)
    service_data = ServiceSerializer(read_only=True, source='service')
    attachments = AttachmentSerializer(many=True)
    answers = AnswerSerializer(many=True)
    date_preferences = QuotePreferenceSerializer(many=True, read_only=False, required=False)
    title = serializers.SerializerMethodField()
    order_pk = serializers.SerializerMethodField()

    class Meta:
        model = models.Quote
        fields = [
            'pk',
            'buyer',
            'buyer_name',
            'buyer_photo',
            'seller',
            'seller_name',
            'seller_photo',
            'service',
            'service_data',
            'attachments',
            'answers',
            'date_preferences',
            'comment',
            'note',
            'exchange_request',
            'price',
            'timeline',
            'revisions',
            'year_of_experience',
            'followers',
            'includes',
            'additional_text',
            'require',
            'title',
            'status',
            'order_pk',
            'created'
        ]
        read_only_fields = [
            'buyer',
            'price',
            'comment',
            'note',
            'exchange_request',
            'price',
            'timeline',
            'revisions',
            'year_of_experience',
            'followers',
            'includes',
            'additional_text',
            'require',
            'created',
            'date_preferences'
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
        date_preferences = validated_data.pop('date_preferences', None)
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
    def get_title(obj):
        if obj.service:
            return obj.service.service_type.name
        if obj.exchange_request:
            return obj.exchange_request.title
        return ''

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

    @staticmethod
    def get_order_pk(obj):
        if hasattr(obj, 'order') and obj.order:
            return obj.order.pk
        return None


class FundingRequestSerializer(serializers.ModelSerializer):
    buyer_name = serializers.SerializerMethodField()
    investor_name = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True)
    answers = AnswerSerializer(many=True)
    investor_process = serializers.CharField(source='investor.investor_services_info.process', read_only=True)

    class Meta:
        model = models.FundingRequest
        fields = [
            'pk',
            'investor',
            'investor_name',
            'investor_process',
            'buyer',
            'buyer_name',
            'attachments',
            'answers',
            'status',
            'created',
            'comments'
        ]
        read_only_fields = [
            'buyer',
            'status',
            'created'
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
    service_data = ServiceSerializer(read_only=True, source='service')
    attachments = AttachmentSerializer(many=True)
    answers = AnswerSerializer(many=True)
    timeline = serializers.SerializerMethodField()
    revisions = serializers.SerializerMethodField()
    order_preferences = OrderPreferenceSerializer(many=True, read_only=False, required=False)

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
            'note',
            'status',
            'title',
            'completed_file',
            'timeline',
            'revisions',
            'order_preferences'
        ]
        read_only_fields = [
            'buyer',
            'status',
            'price',
            'title',
            'completed_file',
            'timeline',
            'revisions'
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

    def create(self, validated_data):
        attachments = validated_data.pop('attachments')
        answers = validated_data.pop('answers')
        order_preferences = validated_data.pop('order_preferences', None)
        instance = super().create(validated_data)
        if attachments:
            self.update_attachments(instance, attachments)
        if answers:
            self.update_answers(instance, answers)
        if order_preferences:
            self.update_preferences(instance, order_preferences)
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

    @staticmethod
    def update_preferences(instance, preferences):
        instance.order_preferences.all().delete()
        for preference in preferences:
            models.OrderPreference.objects.create(
                order=instance,
                date=preference['date'],
                time_start=preference['time_start'],
                time_end=preference['time_end']
            )

    @staticmethod
    def get_timeline(obj):
        if hasattr(obj, 'quote') and obj.quote:
            return obj.quote.timeline
        else:
            return obj.service.timeline

    @staticmethod
    def get_revisions(obj):
        if hasattr(obj, 'quote') and obj.quote:
            return obj.quote.revisions
        else:
            return obj.service.revision



class AttachCompletedFileSerializer(serializers.ModelSerializer):
    completed_file = serializers.FileField(required=False)
    completed_file_base64 = Base64FileField(required=False)

    class Meta:
        model = models.Order
        fields = [
            'completed_file',
            'completed_file_base64'
        ]

    @staticmethod
    def validate(attrs):
        if not (attrs.get('completed_file', None) or attrs.get('completed_file_base64', None)):
            raise serializers.ValidationError(
                {'completed_file': _('This field is required')}
            )
        return attrs


class ReviewSerializer(serializers.ModelSerializer):
    rate = serializers.IntegerField(max_value=5, min_value=1)
    reviewer_name = serializers.CharField(source='buyer.name', read_only=True)
    reviewer_avatar = serializers.FileField(source='buyer.profile.image', read_only=True)

    class Meta:
        model = models.Order
        fields = [
            'rate',
            'review_text',
            'review_datetime',
            'reviewer_name',
            'reviewer_avatar'
        ]


class AcceptOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Order
        fields = [
            'note',
        ]


class ProvideQuoteSerializer(serializers.ModelSerializer):
    price = serializers.IntegerField(max_value=999999, min_value=1)
    timeline = serializers.IntegerField(max_value=99, min_value=1)
    revisions = serializers.IntegerField(max_value=10, min_value=0)

    class Meta:
        model = models.Quote
        fields = [
            'comment',
            'price',
            'timeline',
            'revisions',
            'note',
        ]


class PaymentOrdersSerialier(serializers.Serializer):
    orders = serializers.PrimaryKeyRelatedField(queryset=models.Order.objects.filter(status='created'), many=True)
    stripe_token = serializers.CharField(
        max_length=400,
        write_only=True,
        required=False,
        allow_null=True
    )
    remember_card = serializers.BooleanField(default=False)
    promo_code = serializers.CharField(max_length=50, allow_null=True, allow_blank=True, required=True)
    pay_saved_card = serializers.BooleanField(default=False)

    def validate(self, attrs):
        token = attrs.get('stripe_token')
        saved_card = attrs.get('pay_saved_card')
        if not (token or saved_card):
            raise serializers.ValidationError({
                'stripe_token': _('This field is required'),
                'pay_saved_card': _('This field mast be true if stripe toke is empty')
            })
        return attrs

    def validate_pay_saved_card(self, value):
        user = self.context['request'].user
        if value:
            if not (user.bank_details and user.bank_details.stripe_customer_id):
                raise serializers.ValidationError(
                    _('You do not have saved cards')
                )
        return value


class EmptySerializer(serializers.Serializer):
    pass


class FundingRequestCommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FundingRequest
        fields = (
            'comments',
        )
