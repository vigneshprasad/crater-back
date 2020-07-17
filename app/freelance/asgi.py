import os
import django
import sentry_sdk

from channels.routing import get_default_application
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "freelance.settings")

django.setup()

application = get_default_application()

# Wrapping the app in Sentry WSGI Middleware.
application = SentryAsgiMiddleware(application)
