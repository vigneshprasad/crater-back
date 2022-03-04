from typing import Optional

from aws_cdk import aws_ec2, aws_rds, Duration, NestedStack, RemovalPolicy
from aws_cdk.aws_rds import Credentials, DatabaseInstance, \
    DatabaseInstanceEngine, DatabaseSecret, PostgresEngineVersion
from conf import DB_PORT
from constructs import Construct


class DatabaseStack(NestedStack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            instance_type: aws_ec2.InstanceType,
            multi_az: bool = False,
            backup_retention: int = 1,
            storage_encrypted: bool = False,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.sg = aws_ec2.SecurityGroup(
            self,
            f"{construct_id}-database-sg",
            vpc=scope.vpc,
            security_group_name=f"{construct_id}-db-sg"
        )
        self.sg.add_ingress_rule(self.sg, aws_ec2.Port.tcp(DB_PORT))

        self.db_secret = DatabaseSecret(self, f"{construct_id}/DB_SECRET", username="postgres")
        credentials = Credentials.from_secret(secret=self.db_secret, username="postgres")
        db_engine = DatabaseInstanceEngine.postgres(version=PostgresEngineVersion.VER_14_1)

        self.database = DatabaseInstance(
            self,
            f"{construct_id}-database",
            credentials=credentials,
            instance_identifier=f"{construct_id}-database",
            engine=db_engine,
            allocated_storage=30,
            database_name=construct_id.replace("-", ""),
            instance_type=instance_type,
            multi_az=multi_az,
            vpc=scope.vpc,
            security_groups=[self.sg],
            max_allocated_storage=120,
            backup_retention=Duration.days(amount=backup_retention),
            storage_encrypted=storage_encrypted
        )


class DatabaseClusterStack(NestedStack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            instance_type: aws_ec2.InstanceType,
            instance_count: Optional[int] = 1,
            add_proxy: Optional[bool] = False,
            storage_encrypted: Optional[bool] = False,
            backup_retention: int = 1,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.sg = aws_ec2.SecurityGroup(
            self,
            f"{construct_id}-db-sg",
            vpc=scope.vpc,
            security_group_name=f"{construct_id}-db-sg"
        )

        self.db_secret = DatabaseSecret(self, f"{construct_id}-DB_SECRET", username="postgres")
        credentials = Credentials.from_secret(secret=self.db_secret, username="postgres")
        self.cluster = aws_rds.DatabaseCluster(
            self,
            f"{construct_id}-cluster",
            cluster_identifier=f"{construct_id}-cluster",
            engine=aws_rds.DatabaseClusterEngine.aurora_postgres(
                version=aws_rds.AuroraPostgresEngineVersion.VER_13_4
            ),
            instance_props=aws_rds.InstanceProps(
                vpc=scope.vpc,
                security_groups=[self.sg],
                instance_type=instance_type,
            ),

            credentials=credentials,
            instances=instance_count,

            backup=aws_rds.BackupProps(retention=Duration.days(amount=backup_retention)),
            deletion_protection=False,
            storage_encrypted=storage_encrypted,
            removal_policy=RemovalPolicy.RETAIN,
        )

        if add_proxy:
            self.cluster.add_proxy(
                f"{construct_id}-proxy",
                secrets=[self.db_secret],
                vpc=scope.vpc,
                db_proxy_name=f"proxy-{construct_id}",
                security_groups=[self.sg]
            )
        # if instance_count > 2:
        #     target = autoscaling.ScalableTarget(
        #         self,
        #         f"{construct_id}-scaling-target",
        #         max_capacity=3,
        #         min_capacity=1,
        #         resource_id=self.cluster.cluster_identifier,
        #         # resource_id=f"cluster:{construct_id}-cluster",
        #         scalable_dimension="rds:cluster:ReadReplicaCount",
        #         service_namespace=autoscaling.ServiceNamespace.RDS
        #     )
        #
        #     target.scale_on_metric(
        #         f"{construct_id}-cpu-scaling",
        #         metric=self.cluster.metric_cpu_utilization,
        #         scaling_steps=[
        #             autoscaling.ScalingInterval(upper=80, change=1),
        #             autoscaling.ScalingInterval(upper=40, change=-1),
        #         ],
        #         adjustment_type=autoscaling.AdjustmentType.CHANGE_IN_CAPACITY
        #     )
