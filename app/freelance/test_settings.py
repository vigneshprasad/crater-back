from .settings import *

DEBUG = False

ALLOWED_HOSTS = ['*']


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(ROOT_DIR, "staticfiles")
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(ROOT_DIR, "media")

AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = None
AWS_S3_OBJECT_PARAMETERS = None
AWS_S3_REGION_NAME = 'eu-central-1'
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
AWS_STORAGE_BUCKET_NAME = None
STATIC_LOCATION = None
PUBLIC_MEDIA_LOCATION = None
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'


MANDRILL_API_KEY = None
DEFAULT_EMAIL_FROM = None
DEFAULT_FROM_EMAIL = None


DEFAULT_SMS_PHONE_NUMBER = None
TWILIO_ACCOUNT_SID = None
TWILIO_AUTH_TOKEN = None
ONESIGNAL_APP_ID = None
ONESIGNAL_APIKEY = None

ACCOUNT_LOGOUT_ON_GET = False

ACCOUNT_EMAIL_VERIFICATION = 'none'

MP4_PIPELINE_ID = None
MP4_TRANSCODER_PRESET_ID = None
