from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class StaticStorage(S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False


if settings.AWS_ACCESS_KEY_ID:
    class PrivateMediaStorage(S3Boto3Storage):
        default_acl = 'private'
        file_overwrite = False
        custom_domain = False
else:
   PrivateMediaStorage = lambda: None
