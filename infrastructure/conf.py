import os
from dataclasses import dataclass
from typing import List, Optional

from aws_cdk import aws_logs, Environment
from aws_cdk.aws_ec2 import InstanceClass, InstanceSize, InstanceType
from aws_cdk.aws_logs import RetentionDays

T3_MEDIUM = InstanceType.of(InstanceClass.BURSTABLE3, InstanceSize.MEDIUM)
T3_MICRO = InstanceType.of(InstanceClass.BURSTABLE3, InstanceSize.MICRO)
T3_SMALL = InstanceType.of(InstanceClass.BURSTABLE3, InstanceSize.SMALL)

HTTP_PORT = 80
HTTP_TEST_PORT = 81
HTTPS_PORT = 443
HTTPS_TEST_PORT = 8443
DB_PORT = 5432
REDIS_PORT = 6379
PROD, DEV = "prod", "dev"
BUILD_VERSION = os.environ.get("CI_COMMIT_SHORT_SHA", "latest")


@dataclass()
class Env(Environment):
    account: Optional[str] = None
    region: Optional[str] = None
    environment_name: Optional[str] = None
    # DNS
    hosted_zone_id: Optional[str] = None
    domain_name: Optional[str] = None
    environment_prefix: Optional[str] = None
    # Cloudfront Certificate ARN from us-east-1 region
    certificate_arn: Optional[str] = None
    # Network
    use_nat_gateway: Optional[bool] = False
    # Api
    django_cpu: Optional[str] = "256"
    django_memory: Optional[str] = "1024"
    django_autoscaling_min_capacity: Optional[int] = 1
    django_autoscaling_max_capacity: Optional[int] = 1
    # If Celery is enabled it will be started in separate service
    enable_celery: Optional[bool] = True
    celery_cpu: Optional[str] = "256"
    celery_memory: Optional[str] = "1024"
    log_retention: Optional[RetentionDays] = aws_logs.RetentionDays.ONE_MONTH
    # Cache
    enable_cache: Optional[bool] = True
    # Database
    use_cluster: Optional[bool] = False
    backup_retention: int = 1
    storage_encrypted: Optional[bool] = False
    db_instance_type: InstanceType = T3_MEDIUM
    db_multi_az: bool = False
    db_instance_count: Optional[int] = 1
    # s3
    media_bucket_arn: Optional[str] = ""

    def __post_init__(self):
        if int(self.django_cpu) * 2 > int(self.django_memory):
            raise Exception("Container Memory value has to be at least twice bigger than CPU")


PROJECT_NAME = "worknetwork"
ACCOUNT = os.environ.get("AWS_ACCOUNT_ID", "682452685130")
REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")

DOMAIN = "worknetwork.in"

DEV_ENV = Env(
    account=ACCOUNT,
    region=REGION,
    hosted_zone_id="Z00238263V1C93TGUMBP9",
    domain_name=f"dev.{DOMAIN}",
    django_cpu="256",
    django_memory="1024",
    environment_prefix="api",
    environment_name=DEV,
    db_instance_type=T3_MICRO,
    certificate_arn="arn:aws:acm:us-east-1:682452685130:certificate/a2a42a13-ef12-46cc-92cd-60f056f2aca9"
)

PROD_ENV = Env(
    account=ACCOUNT,
    region=REGION,
    hosted_zone_id="Z0699370CT3MSW55GUDA",
    domain_name=f"prod.{DOMAIN}",
    django_cpu="1024",
    django_memory="2048",
    django_autoscaling_min_capacity=4,
    django_autoscaling_max_capacity=20,
    environment_name=PROD,
    environment_prefix="api",
    use_cluster=True,
    db_instance_type=T3_MEDIUM,
    media_bucket_arn="arn:aws:s3:::1worknetwork-prod",
    certificate_arn="arn:aws:acm:us-east-1:682452685130:certificate/43dae845-f247-46e6-a6c0-6a7cdb278ce7"
)
