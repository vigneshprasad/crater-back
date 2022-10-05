from __future__ import absolute_import, unicode_literals

from freelance.celery import app as celery_app
import freelance.schema

__all__ = ('celery_app',)
