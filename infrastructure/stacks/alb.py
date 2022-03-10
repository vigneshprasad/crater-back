from typing import Optional

import jsii
from aws_cdk import aws_certificatemanager as cert_manager, aws_elasticloadbalancingv2 as load_balancing, aws_route53, \
    Duration, ITaggable, NestedStack
from aws_cdk.aws_ec2 import Port, SecurityGroup, SubnetSelection, SubnetType
from aws_cdk.aws_elasticloadbalancingv2 import ApplicationProtocol, ListenerCertificate
from aws_cdk.aws_route53_targets import LoadBalancerTarget
from conf import HTTP_PORT, HTTP_TEST_PORT, HTTPS_PORT, HTTPS_TEST_PORT
from constructs import Construct


@jsii.implements(ITaggable)
class ALBStack(NestedStack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            environment_prefix: Optional[str] = None,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.alb_sg = SecurityGroup(
            self,
            f"{construct_id}-alb-sg",
            vpc=scope.vpc,
            security_group_name=f"{construct_id}-alb-sg",
            allow_all_outbound=True,
        )
        self.alb_sg.add_ingress_rule(self.alb_sg, Port.all_traffic())
        self.load_balancer = load_balancing.ApplicationLoadBalancer(
            self,
            id=f"{construct_id}-alb",
            http2_enabled=True,
            idle_timeout=Duration.seconds(60),
            security_group=self.alb_sg,
            vpc=scope.vpc,
            internet_facing=True,
            vpc_subnets=SubnetSelection(
                subnet_type=SubnetType.PUBLIC,
                one_per_az=True
            )
        )
        self.http_listener = self.load_balancer.add_listener(
            f"{construct_id}-http-listener",
            port=HTTP_PORT,
            protocol=ApplicationProtocol.HTTP,
        )
        if hosted_zone := getattr(scope, "hosted_zone", None):
            certificate = cert_manager.Certificate(
                self,
                f"{construct_id}-certificate",
                domain_name=f"*.{hosted_zone.zone_name}",
                subject_alternative_names=[f"*.api.{hosted_zone.zone_name}"],
                validation=cert_manager.CertificateValidation.from_dns(hosted_zone)
            )

            certificates = [ListenerCertificate.from_certificate_manager(certificate)]
            self.listener = self.load_balancer.add_listener(
                f"{construct_id}-main-listener",
                port=HTTPS_PORT,
                protocol=ApplicationProtocol.HTTPS,
                certificates=certificates
            )
            self.test_listener = self.load_balancer.add_listener(
                f"{construct_id}-tests-listener",
                port=HTTPS_TEST_PORT,
                protocol=ApplicationProtocol.HTTPS,
                certificates=certificates
            )
            self.http_listener.add_action(
                f"{construct_id}-redirect-action",
                action=load_balancing.ListenerAction.redirect(
                    host="#{host}",
                    port=str(HTTPS_PORT),
                    path="/#{path}",
                    query="#{query}",
                    protocol="HTTPS"
                ))
        else:
            self.listener = self.http_listener
            self.test_listener = self.load_balancer.add_listener(
                f"{construct_id}-tests-listener",
                port=HTTP_TEST_PORT,
                protocol=ApplicationProtocol.HTTP,
            )
