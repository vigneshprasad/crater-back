from pathlib import Path
from typing import Optional

from aws_cdk import aws_iam, aws_lambda, CustomResource
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.custom_resources import Provider
from constructs import Construct


class DeploymentGroup(Construct):

    def __init__(
            self,
            scope,
            construct_id,
            application_name,
            cluster_name,
            deployment_group_name,
            service_name,
            target_group_names,
            prod_traffic_listener_arn,
            test_traffic_listener_arn,
            wait_time: Optional[int] = 5,
            **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)
        service_role = aws_iam.Role(
            self,
            f"{construct_id}-deploy-role",
            assumed_by=aws_iam.ServicePrincipal(service="codedeploy.amazonaws.com"),
            role_name=f"{construct_id}-deploy-role",
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeDeployRoleForECS")
            ]
        )

        provider = Provider(
            self, f"{construct_id}-provider",
            on_event_handler=aws_lambda.Function(
                self, f"{construct_id}",
                code=aws_lambda.Code.from_asset(f"{Path.cwd()}/custom_constructs/lambdas/deployment_group"),
                handler="app.handler",
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                initial_policy=[
                    PolicyStatement(
                        actions=[
                            "codedeploy:TagResource",
                            "codedeploy:GetDeploymentGroup",
                            "codedeploy:UpdateApplication",
                            "codedeploy:UntagResource",
                            "codedeploy:UpdateDeploymentGroup",
                            "codedeploy:CreateDeploymentGroup",
                            "codeDeploy:DeleteDeploymentGroup",
                            "iam:PassRole"
                        ],
                        resources=["*"]
                    )]

            )
        )
        CustomResource(
            self, f"{construct_id}-DeploymentGroup",
            resource_type="Custom::DeploymentGroup",
            properties={
                "deployment_group_name": deployment_group_name,
                "cluster_name": cluster_name,
                "service_name": service_name,
                "application_name": application_name,
                "target_group_names": target_group_names,
                "prod_traffic_listener_arn": prod_traffic_listener_arn,
                "test_traffic_listener_arn": test_traffic_listener_arn,
                "service_role_arn": service_role.role_arn,
                "wait_time": wait_time,
            },
            service_token=provider.service_token
        )
