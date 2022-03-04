import jsii
from aws_cdk import aws_ec2, aws_ecs, aws_route53, aws_s3, CfnOutput, ITaggable, RemovalPolicy, Stack
from aws_cdk.aws_ec2 import Port, SecurityGroup
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
        for peering_vpc_id in env.peering_vpc_ids or []:
            peering_vpc = aws_ec2.Vpc.from_lookup(self, peering_vpc_id, vpc_id=peering_vpc_id)
            connection = aws_ec2.CfnVPCPeeringConnection(
                self, f"{construct_id}-{peering_vpc_id}-peering",
                vpc_id=self.vpc.vpc_id,
                peer_vpc_id=peering_vpc_id,
            )
            for index, subnet in enumerate([*self.vpc.private_subnets, *self.vpc.public_subnets]):
                aws_ec2.CfnRoute(
                    self, f"{peering_vpc_id}-route-{index}",
                    route_table_id=subnet.route_table.route_table_id,
                    destination_cidr_block=peering_vpc.vpc_cidr_block,
                    vpc_peering_connection_id=connection.ref
                )
            route_tables = set(
                subnet.route_table.route_table_id
                for subnet in peering_vpc.private_subnets
            )
            for index, route_table_id in enumerate(route_tables):
                aws_ec2.CfnRoute(
                    self, f"{peering_vpc_id}-elk-route-{index}",
                    route_table_id=route_table_id,
                    destination_cidr_block=self.vpc.vpc_cidr_block,
                    vpc_peering_connection_id=connection.ref
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
        elif not env.peering_vpc_ids:
            self.db = DatabaseStack(
                self,
                f"{construct_id}-db",
                instance_type=T3_MICRO,
                backup_retention=env.backup_retention,
                multi_az=env.db_multi_az,
                storage_encrypted=env.storage_encrypted
            )

        self.alb = ALBStack(self, f"{construct_id}-alb", environment_prefix=env.environment_prefix)

        if env.enable_cache or env.enable_celery:
            self.cache = CacheStack(self, f"{construct_id}-cache")
            self.cache.sg.add_ingress_rule(self.app_sg, Port.tcp(REDIS_PORT))

        if hasattr(self, "db"):
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
        self.media_bucket = aws_s3.Bucket(
            self,
            f"{construct_id}-media-bucket",
            bucket_name=f"{construct_id}-media",
            block_public_access=aws_s3.BlockPublicAccess(restrict_public_buckets=True),
            removal_policy=RemovalPolicy.DESTROY
        )
        self.service = FargateApiServiceStack(
            self,
            f"{construct_id}-django-service",
            task_definition_cpu=env.django_cpu,
            task_definition_memory=env.django_memory,
            log_retention=env.log_retention,
            environment_name=env.environment_name,
            autoscaling_min_capacity=env.django_autoscaling_min_capacity,
            autoscaling_max_capacity=env.django_autoscaling_max_capacity,
            datadog_logging=True
        )
        if env.enable_celery:
            self.celery_service = FargateServiceStack(
                self, f"{construct_id}-celery",
                task_definition_cpu=env.celery_cpu,
                task_definition_memory=env.celery_memory,
                log_retention=env.log_retention,
                environment_name=env.environment_name,
                entry_point=["celery", "-A", "freelance", "worker", "-l", "info", "--concurrency=4", "-B"],
                datadog_logging=True
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
            value=f"https://{self.alb.domain}/"
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
