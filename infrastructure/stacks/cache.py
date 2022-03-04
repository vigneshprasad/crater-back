from aws_cdk import aws_elasticache as elasticache, NestedStack
from aws_cdk.aws_ec2 import SecurityGroup
from constructs import Construct


class CacheStack(NestedStack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.sg = SecurityGroup(
            self,
            f"{construct_id}-cache-sg",
            vpc=scope.vpc,
            security_group_name=f"{construct_id}-cache-sg"
        )

        subnet_group = elasticache.CfnSubnetGroup(
            self, f"{construct_id}-cache-sg-group",
            subnet_ids=[subnet.subnet_id for subnet in scope.vpc.private_subnets],
            cache_subnet_group_name=f"{construct_id}-cache-sg-group",
            description="Redis subnet group"
        )

        self.cache_cluster = elasticache.CfnCacheCluster(
            self, f"{construct_id}-cache",
            cache_node_type="cache.t3.micro",
            engine="redis",
            cluster_name=f"{construct_id}-cache",
            num_cache_nodes=1,
            vpc_security_group_ids=[self.sg.security_group_id],
            cache_subnet_group_name=subnet_group.ref
        )
