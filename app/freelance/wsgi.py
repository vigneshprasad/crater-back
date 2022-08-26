"""
WSGI config for freelance project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""
import os
import sentry_sdk

from django.core.wsgi import get_wsgi_application
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freelance.settings")

application = get_wsgi_application()

# Wrapping the app in Sentry WSGI Middleware.
application = SentryWsgiMiddleware(application)
