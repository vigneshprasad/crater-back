import jsii
from aws_cdk import aws_cloudfront, aws_cloudfront_origins, aws_ec2, aws_ecs, aws_iam, aws_route53, aws_s3, \
    aws_secretsmanager, CfnOutput, \
    Duration, \
    ITaggable, \
    RemovalPolicy, Stack
from aws_cdk.aws_certificatemanager import Certificate
from aws_cdk.aws_ec2 import Port, SecurityGroup
from aws_cdk.aws_route53_targets import CloudFrontTarget
from aws_cdk.aws_s3 import HttpMethods
from cdk_ec2_key_pair import KeyPair
from conf import DB_PORT, Env, REDIS_PORT, T3_MICRO
from constructs import Construct

from stacks import CacheStack, DatabaseStack
from stacks.alb import ALBStack
from stacks.database import DatabaseClusterStack
from stacks.ecs import APP_PORT, FargateApiServiceStack, FargateServiceStack


@jsii.implements(ITaggable)
class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env: Env, **kwargs) -> None:
        super().__init__(scope, construct_id, env=env, **kwargs)

        if env.hosted_zone_id:
            self.hosted_zone = aws_route53.HostedZone.from_hosted_zone_attributes(
                self,
                f"{construct_id}-hosted_zone",
                zone_name=env.domain_name,
                hosted_zone_id=env.hosted_zone_id
            )
        key = KeyPair(
            self, f"{construct_id}-bastion-key",
            name=f"{construct_id}-bastion",
            description=f"{construct_id}-bastion",
            store_public_key=True
        )

        nat_provider = aws_ec2.NatProvider.instance(instance_type=T3_MICRO, key_name=key.key_pair_name)
        if env.use_nat_gateway:
            nat_provider = aws_ec2.NatProvider.gateway()
        self.vpc = aws_ec2.Vpc(
            self,
            f"{construct_id}-vpc",
            cidr="10.0.0.0/24",  # 2^(32(IPv4 total bits) - [16-28]) - 5(AWS reserved) = 123ips
            nat_gateways=1,
            nat_gateway_provider=nat_provider
        )

        self.app_sg = SecurityGroup(
            self,
            f"{construct_id}-app-sg",
            vpc=self.vpc,
            security_group_name=f"{construct_id}-app-sg"
        )
        if env.use_cluster:
            self.db = DatabaseClusterStack(
                self,
                f"{construct_id}-db-cluster",
                backup_retention=env.backup_retention,
                instance_type=env.db_instance_type,
                instance_count=env.db_instance_count,
                storage_encrypted=env.storage_encrypted
            )
        else:
            self.db = DatabaseStack(
                self,
                f"{construct_id}-db",
                instance_type=T3_MICRO,
                backup_retention=env.backup_retention,
                multi_az=env.db_multi_az,
                storage_encrypted=env.storage_encrypted
            )
        CfnOutput(
            self,
            f"{construct_id}-DbSecretArn",
            export_name=f"{construct_id}-DbSecretArn",
            value=self.db.db_secret.secret_arn
        )

        self.alb = ALBStack(self, f"{construct_id}-alb")

        self.distribution = aws_cloudfront.Distribution(
            self,
            f"{construct_id}-distribution",
            certificate=Certificate.from_certificate_arn(self, f"{construct_id}-cloudfront-cert", env.certificate_arn),
            domain_names=[f"{env.environment_prefix}.{env.domain_name}"],
            price_class=aws_cloudfront.PriceClass.PRICE_CLASS_200,
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.LoadBalancerV2Origin(self.alb.load_balancer),
                allowed_methods=aws_cloudfront.AllowedMethods.ALLOW_ALL,
                viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin_request_policy=aws_cloudfront.OriginRequestPolicy.ALL_VIEWER,
                cache_policy=aws_cloudfront.CachePolicy(
                    self, f"{construct_id}-cache-policy",
                    cache_policy_name=f"{construct_id}-cache",
                    default_ttl=Duration.minutes(1),
                    min_ttl=Duration.minutes(1),
                    max_ttl=Duration.days(10),
                    cookie_behavior=aws_cloudfront.CacheCookieBehavior.all(),
                    header_behavior=aws_cloudfront.CacheHeaderBehavior.allow_list(
                        "Authorization"
                    ),
                    query_string_behavior=aws_cloudfront.CacheQueryStringBehavior.allow_list(
                        "page", "limit", "skip", "offset", "p", "page_size"
                    ),
                    enable_accept_encoding_gzip=True,
                    enable_accept_encoding_brotli=True
                )
            )
        )
        aws_route53.ARecord(
            self,
            f"{construct_id}-record",
            record_name=env.environment_prefix,
            zone=self.hosted_zone,
            target=aws_route53.RecordTarget.from_alias(alias_target=CloudFrontTarget(self.distribution))
        )
        self.domain = env.domain_name

        if env.enable_cache or env.enable_celery:
            self.cache = CacheStack(self, f"{construct_id}-cache")
            self.cache.sg.add_ingress_rule(self.app_sg, Port.tcp(REDIS_PORT))

        self.db.sg.add_ingress_rule(self.app_sg, Port.tcp(DB_PORT))
        self.app_sg.add_ingress_rule(self.alb.alb_sg, Port.tcp(APP_PORT))

        self.cluster = aws_ecs.Cluster(
            self, f"{construct_id}-cluster",
            cluster_name=f"{construct_id}-cluster",
            vpc=self.vpc,
            enable_fargate_capacity_providers=True
        )

        self.static_bucket = aws_s3.Bucket(
            self,
            f"{construct_id}-statics-bucket",
            bucket_name=f"{construct_id}-statics",
            public_read_access=True,
            removal_policy=RemovalPolicy.DESTROY,
            cors=[
                aws_s3.CorsRule(
                    allowed_methods=[HttpMethods.GET, HttpMethods.PUT, HttpMethods.POST],
                    allowed_origins=["*"],
                    allowed_headers=["*"]
                )
            ],
        )
        if env.media_bucket_arn:
            self.media_bucket = aws_s3.Bucket.from_bucket_arn(
                self,
                f"{construct_id}-media-bucket",
                bucket_arn=env.media_bucket_arn
            )
        else:
            self.media_bucket = aws_s3.Bucket(
                self,
                f"{construct_id}-media-bucket",
                bucket_name=f"{construct_id}-media",
                block_public_access=aws_s3.BlockPublicAccess(restrict_public_buckets=True),
                removal_policy=RemovalPolicy.DESTROY
            )

        dyte_user = aws_iam.User(
            self, f"{construct_id}-dyte-bucket-user"
        )
        dyte_user_access_key = aws_iam.AccessKey(self, f"{construct_id}-dyte-access-key", user=dyte_user)
        dyte_secret = aws_secretsmanager.Secret(
            self, f"{construct_id}-dyte-access-key-secret",
            secret_string_beta1=aws_secretsmanager.SecretStringValueBeta1.from_token(
                dyte_user_access_key.secret_access_key.to_string())
        )
        self.media_bucket.grant_read_write(dyte_user)
        self.media_bucket.grant_put_acl(dyte_user)
        self.service = FargateApiServiceStack(
            self,
            f"{construct_id}-django-service",
            task_definition_cpu=env.django_cpu,
            task_definition_memory=env.django_memory,
            log_retention=env.log_retention,
            environment_name=env.environment_name,
            autoscaling_min_capacity=env.django_autoscaling_min_capacity,
            autoscaling_max_capacity=env.django_autoscaling_max_capacity,
            datadog_logging=True,
            external_secrets={
                "DYTE_AWS_SECRET_ACCESS_KEY": dyte_secret,
                "DB_SECRET": self.db.db_secret
            },
            env={"DYTE_AWS_ACCESS_KEY_ID": dyte_user_access_key.access_key_id}
        )
        if env.enable_celery:
            self.celery_service = FargateServiceStack(
                self, f"{construct_id}-celery",
                task_definition_cpu=env.celery_cpu,
                task_definition_memory=env.celery_memory,
                log_retention=env.log_retention,
                environment_name=env.environment_name,
                entry_point="celery -A freelance worker -l info --concurrency=4".split(),
                datadog_logging=True,
                celery_beat=True
            )
            CfnOutput(
                self,
                f"{construct_id}-CeleryTaskDefinitionTemplateArn",
                export_name=f"{construct_id}-CeleryTaskDefinitionTemplateArn",
                value=self.celery_service.task_definition.task_definition_arn
            )
            CfnOutput(
                self,
                f"{construct_id}-CeleryService",
                export_name=f"{construct_id}-CeleryService",
                value=f"{construct_id}-celery"
            )

        CfnOutput(
            self,
            f"{construct_id}-DjangoServiceURL",
            export_name=f"{construct_id}-DjangoServiceURL",
            value=f"https://{self.domain}/"
        )
        CfnOutput(
            self,
            f"{construct_id}-ClusterName",
            export_name=f"{construct_id}-ClusterName",
            value=self.cluster.cluster_name
        )

        CfnOutput(
            self,
            f"{construct_id}-ApplicationName",
            export_name=f"{construct_id}-ApplicationName",
            value=self.service.application.application_name
        )
        CfnOutput(
            self,
            f"{construct_id}-TaskDefinitionTemplateArn",
            export_name=f"{construct_id}-TaskDefinitionTemplateArn",
            value=self.service.task_definition.task_definition_arn
        )

        CfnOutput(
            self,
            f"{construct_id}-DjangoContainerName",
            export_name=f"{construct_id}-DjangoContainerName",
            value=self.service.task_definition.default_container.container_name
        )
        CfnOutput(
            self,
            f"{construct_id}-DjangoContainerPort",
            export_name=f"{construct_id}-DjangoContainerPort",
            value=str(self.service.task_definition.default_container.container_port)
        )

        CfnOutput(
            self,
            f"{construct_id}-DeploymentGroupName",
            export_name=f"{construct_id}-DeploymentGroupName",
            value=self.service.deployment_group_name
        )
        CfnOutput(
            self,
            f"{construct_id}-PrivateKeySecretArn",
            export_name=f"{construct_id}-PrivateKeySecretArn",
            value=key.private_key_arn
        )
