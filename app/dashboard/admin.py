import datetime
import dateutil

from django.contrib.admin import register, ModelAdmin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path

from community.groups.models import UserRequest
from community.posts.models import Report
from dashboard.models import Dashboard
from order.models import Order
from services.models import Service


@register(Dashboard)
class ChatAdmin(ModelAdmin):
    icon_name = 'dashboard'
    page_chat_template = 'dashboard/page.html'

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path('', self.page_view, name='%s_%s_changelist' % info),
        ]

    def page_view(self, request):
        now = datetime.datetime.now()
        self._check_permissions(request)
        context = self._get_context(request)
        context['pending_users'] = get_user_model().objects.filter(
            is_approved=False, groups__name__in=['User', 'Investor']
        ).count()
        context['pending_services'] = Service.objects.filter(status='unknown').count()
        context['jobs_to_be_paid'] = Order.objects.filter(status='complete', is_paid=False).count()
        context['jobs_to_be_refunded'] = Order.objects.filter(status='canceled', is_paid=False).count()
        context['group_join'] = UserRequest.objects.filter(is_approved=False).count()
        context['reported_posts'] = Report.objects.count()
        context['registered_users'] = self._get_registered_users_timedelta(now)
        context['created_services'] = self._get_created_services_timedelta(now)
        context['created_orders'] = self._get_created_orders_timedelta(now)
        context['group_joins'] = self._get_group_joins_timedelta(now)
        context['post_reports'] = self._get_post_reports_timedelta(now)
        context['label_months'] = self._get_label_month(now)
        return TemplateResponse(request, self.page_chat_template, context)

    def _check_permissions(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

    def _get_context(self, request):
        return dict(
            self.admin_site.each_context(request),
            title='Dashboard',
        )

    @classmethod
    def _get_registered_users_timedelta(cls, now):
        users = get_user_model().objects.filter(groups__name__in=['User', 'Investor'])
        month1, month2, month3, month4, month5, month6 = cls._month_points(now)
        return [
             users.filter(date_joined__gt=month6, date_joined__lt=month5).count(),
             users.filter(date_joined__gt=month5, date_joined__lt=month4).count(),
             users.filter(date_joined__gt=month4, date_joined__lt=month3).count(),
             users.filter(date_joined__gt=month3, date_joined__lt=month2).count(),
             users.filter(date_joined__gt=month2, date_joined__lt=month1).count(),
             users.filter(date_joined__gt=month1).count(),
        ]

    @classmethod
    def _get_created_services_timedelta(cls, now):
        services = Service.objects.all()
        month1, month2, month3, month4, month5, month6 = cls._month_points(now)
        return [
             services.filter(created__gt=month6, created__lt=month5).count(),
             services.filter(created__gt=month5, created__lt=month4).count(),
             services.filter(created__gt=month4, created__lt=month3).count(),
             services.filter(created__gt=month3, created__lt=month2).count(),
             services.filter(created__gt=month2, created__lt=month1).count(),
             services.filter(created__gt=month1).count(),
        ]

    @classmethod
    def _get_created_orders_timedelta(cls, now):
        orders = Order.objects.all()
        month1, month2, month3, month4, month5, month6 = cls._month_points(now)
        return [
            orders.filter(created__gt=month6, created__lt=month5).count(),
            orders.filter(created__gt=month5, created__lt=month4).count(),
            orders.filter(created__gt=month4, created__lt=month3).count(),
            orders.filter(created__gt=month3, created__lt=month2).count(),
            orders.filter(created__gt=month2, created__lt=month1).count(),
            orders.filter(created__gt=month1).count(),
        ]

    @classmethod
    def _get_group_joins_timedelta(cls, now):
        joins = UserRequest.objects.all()
        month1, month2, month3, month4, month5, month6 = cls._month_points(now)
        return [
            joins.filter(created__gt=month6, created__lt=month5).count(),
            joins.filter(created__gt=month5, created__lt=month4).count(),
            joins.filter(created__gt=month4, created__lt=month3).count(),
            joins.filter(created__gt=month3, created__lt=month2).count(),
            joins.filter(created__gt=month2, created__lt=month1).count(),
            joins.filter(created__gt=month1).count(),
        ]

    @classmethod
    def _get_post_reports_timedelta(cls, now):
        reports = Report.objects.all()
        month1, month2, month3, month4, month5, month6 = cls._month_points(now)
        return [
            reports.filter(created__gt=month6, created__lt=month5).count(),
            reports.filter(created__gt=month5, created__lt=month4).count(),
            reports.filter(created__gt=month4, created__lt=month3).count(),
            reports.filter(created__gt=month3, created__lt=month2).count(),
            reports.filter(created__gt=month2, created__lt=month1).count(),
            reports.filter(created__gt=month1).count(),
        ]

    @staticmethod
    def _get_label_month(now):
        month1 = now - dateutil.relativedelta.relativedelta(months=1)
        month2 = now - dateutil.relativedelta.relativedelta(months=2)
        month3 = now - dateutil.relativedelta.relativedelta(months=3)
        month4 = now - dateutil.relativedelta.relativedelta(months=4)
        month5 = now - dateutil.relativedelta.relativedelta(months=5)
        return [
             month5.strftime('%B'),
             month4.strftime('%B'),
             month3.strftime('%B'),
             month2.strftime('%B'),
             month1.strftime('%B'),
             now.strftime('%B'),
        ]

    @staticmethod
    def _month_points(now):
        month1 = now.replace(day=1)
        month2 = month1 - dateutil.relativedelta.relativedelta(months=1)
        month3 = month2 - dateutil.relativedelta.relativedelta(months=1)
        month4 = month3 - dateutil.relativedelta.relativedelta(months=1)
        month5 = month4 - dateutil.relativedelta.relativedelta(months=1)
        month6 = month5 - dateutil.relativedelta.relativedelta(months=1)
        return month1, month2, month3, month4, month5, month6
