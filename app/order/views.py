from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from payment.models import Transaction, StripePaymentIntent
from users import permissions
from utils.stripe_service import stripe_service
from . import models, paginators, serializers


class BuyerOrderViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Quote.objects.none()
        return self.request.user.buyer_orders.exclude(status='created')

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()

    @action(
        methods=['post'],
        serializer_class=serializers.PaymentOrdersSerialier,
        permission_classes=[permissions.IsAuthenticated],
        detail=False
    )
    def pay(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        orders = serializer.validated_data['orders']
        amount = sum([order.price for order in orders])
        amount = amount * 100  # Convert amount to stripe. Stripe get amount in coins
        # TODO: Calculate amount with promo code discount
        orders_id = ', '.join([str(order.pk) for order in orders])
        description = f'Payment for {orders_id}'
        charge = None
        if serializer.validated_data['remember_card']:
            if request.user.bank_details and request.user.bank_details.stripe_customer_id:
                stripe_service.update_customer_source(
                    request.user.bank_details.stripe_customer_id,
                    serializer.validated_data['stripe_token']
                )
            else:
                stripe_customer_id = stripe_service.get_customer_id(
                    request.user,
                    serializer.validated_data['stripe_token']
                )
                request.user.bank_details.stripe_customer_id = stripe_customer_id
                request.user.bank_details.card_data = stripe_service.get_customer_card_data(stripe_customer_id)
                request.user.save()
        if serializer.validated_data['pay_saved_card'] or serializer.validated_data['remember_card']:
            charge = stripe_service.create_customer_charge(
                customer_id=self.request.user.bank_details.stripe_customer_id,
                amount=amount,
                description=description
            )
        elif serializer.validated_data['stripe_token']:
            charge = stripe_service.create_token_charge(
                token=serializer.validated_data['stripe_token'],
                amount=amount,
                description=description,
                user=request.user
            )
        if charge and charge.paid:
            for order in orders:
                order.status = 'pending'
                order.save()
                if hasattr(order, 'quote') and order.quote:
                    order.quote.status = 'accepted'
                    order.quote.save()
                Transaction.objects.create(
                    user=order.buyer,
                    amount=order.price,
                    order=order,
                    direction='in',
                    status='transferred'
                )
        else:
            raise serializers.serializers.ValidationError(
                {'message': _('Create payment error. Connect with support')}
            )
        return Response({'message': _('Successfully paid')})

    @action(
        methods=['post'],
        serializer_class=serializers.GetPaymentIntentSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=False
    )
    def get_payment_intent(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        orders = serializer.validated_data['orders']
        amount = sum([order.price for order in orders])
        amount = amount * 100  # Convert amount to stripe. Stripe get amount in coins
        # TODO: Calculate amount with promo code discount
        orders_id = ', '.join([str(order.pk) for order in orders])
        description = f'Payment for {orders_id}'
        payment_intent = stripe_service.create_payment_intent(
            amount=amount,
            description=description,
            receipt_email=request.user.email
        )
        payment_intent = StripePaymentIntent.objects.create(
            stripe_id=payment_intent['id'],
            status=payment_intent['status'],
            data=payment_intent,
            user=request.user
        )
        payment_intent.orders.add(*orders)
        return Response({'payment_intent_id': payment_intent['id']})

    @action(
        methods=['post'],
        serializer_class=serializers.CheckPaymentIntentSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=False
    )
    def check_payment_intent(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        intent = serializer.validated_data['payment_intent']
        status = intent.check_status(commit=True)
        if status == 'succeeded':
            for order in intent.orders:
                order.status = 'pending'
                order.save()
                if hasattr(order, 'quote') and order.quote:
                    order.quote.status = 'accepted'
                    order.quote.save()
                Transaction.objects.create(
                    user=order.buyer,
                    amount=order.price,
                    order=order,
                    direction='in',
                    status='transferred'
                )
        return Response({'payment_intent_id': intent.stripe_id, 'status': intent.status})

    @action(
        methods=['post'],
        serializer_class=serializers.ReviewSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def add_review(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = self.get_queryset().filter(status__in=['accepted', 'done'])
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.rate = serializer.validated_data['rate']
            instance.review_text = serializer.validated_data['review_text']
            instance.review_datetime = timezone.now()
            instance.status = 'complete'
            instance.save()
            if instance.service:
                instance.service.recalculate_rating()
            instance.seller.recalculate_rating()
        except models.Order.DoesNotExist:
            raise NotFound
        return Response(
            serializers.OrderSerializer(instance, **{'context': context}).data
        )


class SellerOrderViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Order.objects.none()
        return self.request.user.seller_orders.exclude(status='created')

    @action(
        methods=['post'],
        serializer_class=serializers.AcceptOrderSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def accept(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'accepted'
            note = serializer.validated_data.get('note')
            if note:
                instance.note = note
            instance.save()
            if instance.quote:
                instance.quote.status = 'accepted'
                instance.quote.save()
                if instance.quote.exchange_request:
                    other_quotes = (
                        models.Quote.objects
                        .filter(exchange_request=instance.quote.exchange_request)
                        .exclude(pk=instance.quote.pk)
                    )
                    other_quotes.update(status='canceled')
        except models.Order.DoesNotExist:
            raise NotFound
        return Response(
            serializers.OrderSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=serializers.EmptySerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.save()
        except models.Order.DoesNotExist:
            raise NotFound
        return Response(
            serializers.OrderSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=serializers.EmptySerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def done(self, request, pk):
        queryset = self.get_queryset().filter(status='accepted')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'done'
            instance.save()
        except models.Order.DoesNotExist:
            raise NotFound
        return Response(
            serializers.OrderSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=serializers.AttachCompletedFileSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def attach(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = self.get_queryset().filter(status__in=['accepted', 'done'])
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            file = serializer.validated_data.get('completed_file', None)
            if not file:
                file = serializer.validated_data.get('completed_file_base64', None)
            instance.completed_file = file
            instance.status = 'done'
            instance.save()
        except models.Order.DoesNotExist:
            raise NotFound
        return Response(
            serializers.OrderSerializer(instance, **{'context': context}).data
        )


class CartOrderViewSet(mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       mixins.DestroyModelMixin,
                       # mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    queryset = models.Order.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.OrderSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Order.objects.none()
        return self.request.user.buyer_orders.filter(
            status='created',
            quote__isnull=True
        )

    def destroy(self, request, *args, **kwargs):
        """
        Delete order from cart
        """
        data = {}
        try:
            order = models.Order.objects.get(uuid=kwargs['pk'])
            data = self.get_serializer(order).data
            order.delete()
        except models.Order.DoesNotExist:
            raise NotFound
        return Response(status=status.HTTP_200_OK, data=data)


class BuyerQuoteViewSet(mixins.RetrieveModelMixin,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    queryset = models.Quote.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.QuoteSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Quote.objects.none()
        return self.request.user.buyer_quotes.exclude(exchange_request__isnull=False)

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()

    @action(
        methods=['post'],
        serializer_class=serializers.EmptySerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def accept(self, request, pk):
        """
        Create order for quote if order does not exists
        Order pk user for payment
        After successfully payment status changed to accepted
        """
        queryset = self.request.user.buyer_quotes.filter(status='provided')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            if not (hasattr(instance, 'order') and instance.order):
                models.Order.objects.create(
                    buyer=instance.buyer,
                    seller=instance.seller,
                    quote=instance,
                    service=instance.service
                )
        except models.Quote.DoesNotExist:
            raise NotFound
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=serializers.EmptySerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        queryset = self.request.user.buyer_quotes.filter(status='provided')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.save()
        except models.Quote.DoesNotExist:
            raise NotFound
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )


class SellerQuoteViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    queryset = models.Quote.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.QuoteSerializer
    pagination_class = paginators.Pagination
    filterset_fields = ['status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.Quote.objects.none()
        return self.request.user.seller_quotes.all()

    @action(
        methods=['post'],
        serializer_class=serializers.ProvideQuoteSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def provide(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'provided'
            instance.price = serializer.validated_data['price']
            instance.comment = serializer.validated_data['comment']
            instance.timeline = serializer.validated_data['timeline']
            instance.revisions = serializer.validated_data['revisions']
            instance.note = serializer.validated_data['note']
            instance.save()
        except models.Quote.DoesNotExist:
            raise NotFound
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=serializers.EmptySerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.save()
        except models.Quote.DoesNotExist:
            raise NotFound
        return Response(
            serializers.QuoteSerializer(instance, **{'context': context}).data
        )


class BuyerFundingRequestViewSet(mixins.RetrieveModelMixin,
                                 mixins.ListModelMixin,
                                 mixins.CreateModelMixin,
                                 viewsets.GenericViewSet):
    queryset = models.FundingRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingRequestSerializer
    pagination_class = paginators.Pagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.FundingRequest.objects.none()
        return self.request.user.buyer_funding_requests.all()

    def perform_create(self, serializer):
        serializer.validated_data['buyer'] = self.request.user
        serializer.save()


class InvestorFundingRequestViewSet(mixins.RetrieveModelMixin,
                                    mixins.ListModelMixin,
                                    viewsets.GenericViewSet):
    queryset = models.FundingRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.FundingRequestSerializer
    pagination_class = paginators.Pagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # queryset just for schema generation metadata
            return models.FundingRequest.objects.none()
        return self.request.user.funding_requests.all()

    @action(
        methods=['post'],
        serializer_class=serializers.FundingRequestCommentsSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def accept(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = self.get_queryset().filter(status='pending')
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'accepted'
            instance.comments = serializer.validated_data['comments']
            instance.save()
        except models.FundingRequest.DoesNotExist:
            raise NotFound
        return Response(
            serializers.FundingRequestSerializer(instance, **{'context': context}).data
        )

    @action(
        methods=['post'],
        serializer_class=serializers.FundingRequestCommentsSerializer,
        permission_classes=[permissions.IsAuthenticated],
        detail=True
    )
    def cancel(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = self.get_queryset().filter(status__in=['pending'])
        context = self.get_serializer_context()
        try:
            instance = queryset.get(pk=pk)
            instance.status = 'canceled'
            instance.comments = serializer.validated_data['comments']
            instance.save()
        except models.FundingRequest.DoesNotExist:
            raise NotFound
        return Response(
            serializers.FundingRequestSerializer(instance, **{'context': context}).data
        )
