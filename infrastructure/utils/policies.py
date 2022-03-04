from typing import List, Optional

import constructs
from aws_cdk import aws_iam as iam
from aws_cdk.aws_iam import PolicyStatement


def ssm_policies(resources: Optional[List[str]] = None) -> List[PolicyStatement]:
    return [
        PolicyStatement(resources=resources or ["*"],
                        actions=[
                            "ssm:GetParameters",
                            "ssm:GetParameter",
                            "ssm:GetParametersByPath",
                        ]
                        ),
        PolicyStatement(resources=["*"], actions=["ssm:DescribeParameters"])
    ]


def secrets_manager_statements(resources: Optional[List[str]] = None) -> List[PolicyStatement]:
    return [
        PolicyStatement(resources=resources or ["*"],
                        actions=[
                            "secretsmanager:GetRandomPassword",
                            "secretsmanager:GetResourcePolicy",
                            "secretsmanager:GetSecretValue",
                            "secretsmanager:DescribeSecret", ]
                        ),
        PolicyStatement(resources=["*"],
                        actions=[
                            "secretsmanager:ListSecretVersionIds",
                            "secretsmanager:ListSecrets"]
                        )
    ]


def s3_statement(resources: Optional[List[str]] = None) -> PolicyStatement:
    return PolicyStatement(
        resources=resources or ["*"],
        actions=["s3:PutObject",
                 "s3:GetObjectAcl",
                 "s3:GetObject",
                 "s3:DeleteObject",
                 "s3:GetBucketAcl",
                 "s3:GetBucketPolicy",
                 ]
    )


def logs_statement(resources: Optional[List[str]] = None) -> PolicyStatement:
    return PolicyStatement(
        resources=resources or ["*"],
        actions=["logs:CreateLogGroup",
                 "logs:PutLogEvents",
                 "logs:CreateLogStream",
                 ]
    )


def ecr_statements(resources: Optional[List[str]] = None) -> List[PolicyStatement]:
    return [
        iam.PolicyStatement(
            actions=[
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:BatchCheckLayerAvailability",
            ],
            resources=resources or ["*"]
        ),
        iam.PolicyStatement(
            actions=["ecr:GetAuthorizationToken"],
            resources=["*"]
        )
    ]


def ses_statement(resources: Optional[List[str]] = None) -> PolicyStatement:
    return iam.PolicyStatement(
        actions=[
            "ses:SendRawEmail",
            "ses:SendEmail",
            "ses:SendTemplatedEmail",
        ],
        resources=resources or ["*"]
    )


class ExecutionRole(iam.Role):

    def __init__(
            self,
            scope: constructs.Construct,
            construct_id: str,
            **kwargs,
    ) -> None:
        managed_policies = [
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmazonECSTaskExecutionRolePolicy")
        ]
        super().__init__(
            scope,
            f"{construct_id}-execution",
            **kwargs,
            assumed_by=iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
            role_name=f"{construct_id}-execution",
            managed_policies=managed_policies + kwargs.get("managed_policies", [])
        )


class TaskRole(iam.Role):

    def __init__(
            self,
            scope: constructs.Construct,
            construct_id: str,
            **kwargs,
    ) -> None:
        super().__init__(
            scope,
            f"{construct_id}-task-role",
            **kwargs,
            assumed_by=iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
            role_name=f"{construct_id}-task-role"
        )


class CodeDeployRole(iam.Role):

    def __init__(
            self,
            scope: constructs.Construct,
            construct_id: str,
            **kwargs,
    ) -> None:
        super().__init__(
            scope,
            f"{construct_id}-codedeploy-role",
            **kwargs,
            assumed_by=iam.ServicePrincipal(service="codedeploy.amazonaws.com"),
            role_name=f"{construct_id}-codedeploy-role-for-ecs",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeDeployRoleForECS")
            ]
        )
