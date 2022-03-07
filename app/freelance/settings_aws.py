import json

from .settings import *

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
BUILD_VERSION = os.environ.get("BUILD_VERSION", "latest")
ROOT_DOMAIN = os.environ['ROOT_DOMAIN']

AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")

# S3 storage
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", AWS_DEFAULT_REGION)
AWS_TRANSCODER_REGION_NAME = os.getenv("AWS_TRASCODER_REGION_NAME", AWS_DEFAULT_REGION)
AWS_DEFAULT_ACL = "public-read"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
# Static
AWS_STATIC_BUCKET_NAME = os.environ.get("STATIC_BUCKET_NAME")
STATIC_ROOT = os.getenv('STATIC_ROOT', os.path.join(BASE_DIR, 'static/'))
STATICFILES_STORAGE = "utils.storage_backends.NewStaticStorage"

# Media
AWS_STORAGE_BUCKET_NAME = os.environ.get("STORAGE_BUCKET_NAME")
AWS_DEFAULT_OBJECT_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media/'))
PUBLIC_MEDIA_LOCATION = "media"
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
DEFAULT_FILE_STORAGE = "utils.storage_backends.PublicMediaStorage"

# RDS config
if os.getenv("DB_SECRET"):
    DB_CONF = json.loads(os.getenv("DB_SECRET"))
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": os.getenv("DB_NAME", DB_CONF.get("dbname")),
            "USER": DB_CONF["username"],
            "HOST": DB_CONF["host"],
            "PASSWORD": DB_CONF["password"],
            "PORT": DB_CONF["port"],
        }
    }
    if reader_host := DB_CONF.get("reader_host"):
        DATABASE_ROUTERS = ['apps.utils.routers.ReaderRouter']
        DATABASES["reader"] = {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": os.getenv("DB_NAME", DB_CONF.get("dbname")),
            "USER": DB_CONF["username"],
            "HOST": reader_host,
            "PASSWORD": DB_CONF["password"],
            "PORT": DB_CONF["port"]
        }

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, 6379)],
        },
    },
}
REDIS = redis.Redis(host=REDIS_HOST, port=6379)

CRATER_FRONT_URL = os.environ.get("CRATER_FRONT_URL", "https://penitence-pre-prod.vercel.app/")
FERNET_KEY = os.environ.get("FERNET_KEY")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"console": {"format": "[%(asctime)s] level=%(levelname)-7s module=%(name)s  %(message)s"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": "INFO",

        },
        'ddtrace': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}
