from rest_framework import serializers

from services.models import Service
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


class OrderServiceSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True)
    answers = AnswerSerializer(many=True)
    service_pk = serializers.PrimaryKeyRelatedField(queryset=Service.objects.filter(status='approved'), write_only=True)

    class Meta:
        model = models.OrderService
        fields = (
            'service',
            'attachments',
            'answers',
            'service_pk'
        )


class OrderSerializer(serializers.ModelSerializer):
    buyer_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    services = OrderServiceSerializer(many=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = models.Order
        fields = [
            'pk',
            'buyer',
            'buyer_name',
            'seller',
            'seller_name',
            'services',
            'price'
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

    @staticmethod
    def get_price(obj):
        order_services = obj.services.all()
        price = sum(list([service.service.price if service.service.price else 0 for service in order_services]))
        return price

    def create(self, validated_data):
        services = validated_data.pop('services')
        instance = super().create(validated_data)
        if services:
            self.update_services(instance, services)
        return instance

    def update_services(self, instance, services):
        instance.services.all().delete()
        for service in services:
            order_service = models.OrderService.objects.create(
                order=instance,
                service=service['service_pk']
            )
            attachments = service.pop('attachments')
            answers = service.pop('answers')
            if attachments:
                self.update_attachments(order_service, attachments)
            if answers:
                self.update_answers(order_service, answers)

    @staticmethod
    def update_attachments(instance, attachments):
        instance.attachments.all().delete()
        for attachment in attachments:
            attach = models.Attachment.objects.create(
                order_service=instance,
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
                order_service=instance,
                question=answer['question'],
                text=answer['text']
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

