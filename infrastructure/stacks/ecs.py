import os
from copy import copy
from typing import Dict, Optional

import jsii
from aws_cdk import aws_ecr, aws_ecs, aws_iam, aws_logs, aws_secretsmanager as secretsmanager, aws_ssm, Duration, Fn, \
    ITaggable, \
    NestedStack, RemovalPolicy
from aws_cdk.aws_codedeploy import EcsApplication
from aws_cdk.aws_ecs import Compatibility, ContainerImage, DeploymentController, DeploymentControllerType, \
    FargatePlatformVersion, FargateService, NetworkMode, PortMapping, TaskDefinition
from aws_cdk.aws_elasticloadbalancingv2 import ApplicationProtocol, HealthCheck
from aws_cdk.aws_logs import LogGroup
from conf import BUILD_VERSION, PROJECT_NAME, REGION
from constructs import Construct
from custom_constructs.deployment_group import DeploymentGroup
from utils.policies import ExecutionRole, ssm_policies, TaskRole

APP_PORT = 8000


@jsii.implements(ITaggable)
class FargateApiServiceStack(NestedStack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            task_definition_cpu: str,
            task_definition_memory: str,
            environment_name: str,
            log_retention: aws_logs.RetentionDays = aws_logs.RetentionDays.ONE_MONTH,
            autoscaling_min_capacity: int = 1,
            autoscaling_max_capacity: int = 1,
            entry_point: Optional[list] = None,
            datadog_logging: Optional[bool] = False,
            external_secrets: Optional[Dict[str, secretsmanager.Secret]] = None,
            env: Optional[dict] = None,
            **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.service = FargateService(
            self,
            id=f"{construct_id}-service",
            service_name=construct_id,
            cluster=scope.cluster,
            task_definition=self.create_dummy_task_definition(construct_id),
            platform_version=FargatePlatformVersion.VERSION1_4,
            security_groups=[scope.app_sg],
            deployment_controller=DeploymentController(type=DeploymentControllerType.CODE_DEPLOY),
            desired_count=0,
            health_check_grace_period=Duration.seconds(60),
            max_healthy_percent=200,
            min_healthy_percent=100
        )
        scaling = self.service.auto_scale_task_count(
            min_capacity=autoscaling_min_capacity,
            max_capacity=autoscaling_max_capacity,

        )

        self.execution_role = ExecutionRole(self, construct_id)
        for policy_statement in ssm_policies():
            self.execution_role.add_to_policy(statement=policy_statement)

        self.task_definition = aws_ecs.TaskDefinition(
            self,
            f"{construct_id}-taskdef-{BUILD_VERSION}",
            task_role=TaskRole(
                self, construct_id,
                managed_policies=[
                    aws_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonElasticTranscoder_FullAccess")
                ]
            ),
            execution_role=self.execution_role.without_policy_updates(),
            cpu=task_definition_cpu,
            memory_mib=task_definition_memory,
            network_mode=aws_ecs.NetworkMode.AWS_VPC,
            family=construct_id,
            compatibility=aws_ecs.Compatibility.FARGATE
        )

        scope.static_bucket.grant_read_write(self.task_definition.task_role)
        scope.static_bucket.grant_put_acl(self.task_definition.task_role)
        scope.media_bucket.grant_read_write(self.task_definition.task_role)
        scope.media_bucket.grant_put_acl(self.task_definition.task_role)

        # Different parameters, client ids, secure urls (Wont be visible in task definition)
        additional_parameters = [
            "CRATER_FRONT_URL",
            "MANDRILL_API_KEY",
            "FERNET_KEY",
            "ALLOW_MESSAGE_SENDING",
            "DEFAULT_SMS_PHONE_NUMBER",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "ONESIGNAL_APP_ID",
            "ONESIGNAL_APIKEY",
            "STRIPE_API_KEY",
            "SEGMENT_WRITE_KEY",
            "FRONT_URL",
            "MP4_PIPELINE_ID",
            "MP4_TRANSCODER_PRESET_ID",
            "SOCIAL_AUTH_APPLE_KEY_ID",
            "SOCIAL_AUTH_APPLE_TEAM_ID",
            "SOCIAL_AUTH_APPLE_CLIENT_ID",
            "SOCIAL_AUTH_APPLE_PRIVATE_KEY",
            "GOOGLE_BUNDLE_ID",
            "GOOGLE_SERVICE_ACCOUNT_KEY_FILE",
            "APPLE_BUNDLE_ID",
            "INSTAGRAM_API_CLIENT_ID",
            "INSTAGRAM_API_CLIENT_SECRET",
            "INSTAGRAM_REDIRECT_URL",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
            "SENTRY_DNS",
            "FRESHCHAT_APP_ID",
            "FRESHCHAT_MESSAGING_PHONE_NUMBER",
            "FRESHCHAT_WHATSAPP_NAMESPACE",
            "FRESHCHAT_ACCESS_TOKEN",
            "GOOGLE_API_ACCOUNT_TYPE",
            "GOOGLE_API_PROJECT_ID",
            "GOOGLE_API_PRIVATE_KEY_ID",
            "GOOGLE_API_PRIVATE_KEY",
            "GOOGLE_API_CLIENT_EMAIL",
            "GOOGLE_API_CLIENT_ID",
            "GOOGLE_API_AUTH_URI",
            "GOOGLE_API_TOKEN_URI",
            "GOOGLE_API_AUTH_PROVIDER_CERT_URL",
            "GOOGLE_API_CLIENT_CERT_URL",
            "FIREBASE_ACCOUNT_PRIVATE_KEY_ID",
            "FIREBASE_ACCOUNT_PRIVATE_KEY",
            "FIREBASE_AUTH_PROVIDER_CERT_URL",
            "FIREBASE_CLIENT_ID",
            "SUPERPRO_ACCESS_TOKEN",
            "AGORA_APP_ID",
            "AGORA_APP_CERTIFICATE",
            "DYTE_ORG_ID",
            "DYTE_APP_ID",
            "STRIPE_PUBLISHABLE_KEY",
            "STRIPE_SECRET_KEY",
            "DEFAULT_FROM_EMAIL"
        ]

        params = {
            parameter_name: aws_ecs.Secret.from_ssm_parameter(
                aws_ssm.StringParameter(
                    self, f"{construct_id}-{parameter_name}",
                    parameter_name=f"/{environment_name.upper()}/{parameter_name}",
                    string_value=os.environ.get(parameter_name, parameter_name)
                )
            ) for parameter_name in additional_parameters
        }

        # Only for most important secrets e.g DB secrets, Social auth secrets, api keys
        additional_secrets = [
            "SECRET_KEY",
        ]
        secrets = {**external_secrets} if external_secrets else {}
        for secret_name in additional_secrets:
            secrets[secret_name] = secretsmanager.Secret(
                self, f"{construct_id}-{secret_name}",
                secret_name=f"/{environment_name.upper()}/{secret_name}",
            )
        for secret_name, secret in secrets.items():
            secret.grant_read(self.execution_role)
            secrets[secret_name] = aws_ecs.Secret.from_secrets_manager(secret)

        self.secrets = {
            **params,
            **secrets,
        }

        # Non sensitive data
        self.container_environment = {
            "DJANGO_SETTINGS_MODULE": "freelance.settings_aws",
            "ENVIRONMENT": environment_name,
            "ROOT_DOMAIN": scope.domain,
            "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", REGION),
            "BUILD_VERSION": BUILD_VERSION,
            "LOCAL_CURRENCY": "inr",
            "LOCAL_COUNTRY": "IN",
            "AWS_STORAGE_BUCKET_NAME": scope.media_bucket.bucket_name,
            "STATIC_BUCKET_NAME": scope.static_bucket.bucket_name,
            "DD_ENV": environment_name,
            "DD_SERVICE": construct_id,
            "DD_VERSION": BUILD_VERSION,
            **env
        }

        if hasattr(scope, "cache"):
            self.container_environment["REDIS_HOST"] = scope.cache.cache_cluster.attr_redis_endpoint_address

        self.repository = aws_ecr.Repository.from_repository_name(
            self,
            f"{construct_id}-repository-connection",
            repository_name=Fn.import_value(f"{PROJECT_NAME}-RepositoryName")
        )

        dd_api_secret = secretsmanager.Secret.from_secret_name_v2(
            self, f"{construct_id}-DD_API_KEY",
            secret_name="DD_API_KEY",
        )
        dd_api_secret.grant_read(self.execution_role)
        logging = aws_ecs.FireLensLogDriver(
            options={
                "Name": "datadog",
                "dd_service": construct_id,
                "dd_source": "httpd",
                "dd_version": BUILD_VERSION,
                "dd_env": environment_name,
                "provider": "ecs",
                "apikey": dd_api_secret.secret_value.to_string(),
                "Host": "http-intake.logs.datadoghq.eu",
                "dd_message_key": "log",
                "TLS": "on",
            }
        )
        self.log_group = LogGroup(
            self,
            f"{construct_id}-logs",
            log_group_name=f"ecs/{construct_id}",
            removal_policy=RemovalPolicy.DESTROY,
            retention=log_retention,
        )
        self.log_group.grant_write(self.task_definition.task_role)

        self.task_definition.add_container(
            f"{construct_id}-django",
            image=aws_ecs.ContainerImage.from_ecr_repository(
                repository=self.repository,
                tag=BUILD_VERSION
            ),
            port_mappings=[aws_ecs.PortMapping(container_port=APP_PORT, host_port=APP_PORT)],
            logging=logging,
            secrets=self.secrets,
            environment=self.container_environment,
            entry_point=entry_point,
            docker_labels={
                "com.datadoghq.ad.instances": str([{"host": "%%host%%", "port": APP_PORT}]),
                "com.datadoghq.tags.env": environment_name,
                "com.datadoghq.tags.service": construct_id,
                "com.datadoghq.tags.version": BUILD_VERSION,
            }
        )
        aws_logs = aws_ecs.LogDriver.aws_logs(
            stream_prefix="ecs",
            log_group=self.log_group
        )
        self.task_definition.add_container(
            f"{construct_id}-datadog",
            container_name="datadog-agent",
            logging=aws_logs,
            image=aws_ecs.ContainerImage.from_registry("gcr.io/datadoghq/agent:latest"),
            port_mappings=[aws_ecs.PortMapping(container_port=8126, host_port=8126)],
            environment={
                "SD_BACKEND": "docker",
                "ECS_FARGATE": "true",
                "DD_APM_ENABLED": "true",
                "DD_SITE": "datadoghq.eu",
                "DD_APM_NON_LOCAL_TRAFFIC": "true"
            },
            secrets={
                "DD_API_KEY": aws_ecs.Secret.from_secrets_manager(dd_api_secret)
            }

        )

        if datadog_logging:
            self.task_definition.add_firelens_log_router(
                f"{construct_id}-router",
                logging=aws_logs,
                firelens_config=aws_ecs.FirelensConfig(
                    type=aws_ecs.FirelensLogRouterType.FLUENTBIT,
                    options=aws_ecs.FirelensOptions(
                        enable_ecs_log_metadata=True,
                        config_file_type=aws_ecs.FirelensConfigFileType.FILE,
                        config_file_value="/fluent-bit/configs/parse-json.conf",
                    )
                ),
                image=aws_ecs.ContainerImage.from_registry(
                    name="906394416424.dkr.ecr.ap-south-1.amazonaws.com/aws-for-fluent-bit:latest"
                )
            )

        self.task_definition.apply_removal_policy(RemovalPolicy.RETAIN)
        # Add Load balancer targets
        # Full name Can't be longer than 32 symbols
        target_group_prefix = construct_id[:19]
        target_group_blue = scope.alb.listener.add_targets(
            f"{construct_id}-tg-blue",
            target_group_name=f"{target_group_prefix}-tg-blue",
            protocol=ApplicationProtocol.HTTP,
            port=APP_PORT,
            health_check=HealthCheck(path="/api/build-version/", unhealthy_threshold_count=5),
            targets=[self.service]
        )
        target_group_green = scope.alb.test_listener.add_targets(
            f"{construct_id}-tg-green",
            target_group_name=f"{target_group_prefix}-tg-green",
            protocol=ApplicationProtocol.HTTP,
            port=APP_PORT,
            health_check=HealthCheck(path="/api/build-version/", unhealthy_threshold_count=5),
            targets=[self.service]
        )

        scaling.scale_on_request_count(
            f"{construct_id}-cpu-scaling",
            requests_per_target=20,
            target_group=target_group_blue
        )

        # Create Blue Green Deployment Application
        self.application = EcsApplication(self, f"{construct_id}-app", application_name=f"{construct_id}-application")
        self.deployment_group_name = f"{construct_id}-group"
        self.deployment_group = DeploymentGroup(
            self,
            f"{construct_id}-deployment-group",
            deployment_group_name=self.deployment_group_name,
            cluster_name=self.service.cluster.cluster_name,
            application_name=self.application.application_name,
            service_name=self.service.service_name,
            prod_traffic_listener_arn=scope.alb.listener.listener_arn,
            test_traffic_listener_arn=scope.alb.test_listener.listener_arn,
            target_group_names=[target_group_blue.target_group_name, target_group_green.target_group_name],
        )

    def create_dummy_task_definition(self, construct_id: str) -> TaskDefinition:
        """
        Dummy Task Definition since updates are not supported for Blue Green deployment type
        So this part can't be changed
        """
        task_definition = TaskDefinition(
            self,
            f"{construct_id}-dummy-taskdef",
            cpu="256",
            memory_mib="512",
            execution_role=ExecutionRole(self, f"{construct_id}-dummy"),
            network_mode=NetworkMode.AWS_VPC,
            family=construct_id,
            compatibility=Compatibility.FARGATE,
        )
        task_definition.add_container(
            f"{construct_id}-dummy-container",
            port_mappings=[PortMapping(container_port=8000, host_port=8000)],
            image=ContainerImage.from_registry(
                name="mendhak/http-https-echo:18"
            ),
            environment={"HTTP_PORT": "8000"}

        )
        return task_definition


@jsii.implements(ITaggable)
class FargateServiceStack(NestedStack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            task_definition_cpu: str,
            task_definition_memory: str,
            environment_name: str,
            desired_count: Optional[int] = 1,
            log_retention: Optional[aws_logs.RetentionDays] = aws_logs.RetentionDays.ONE_MONTH,
            autoscaling_min_capacity: int = 1,
            autoscaling_max_capacity: int = 1,
            entry_point: Optional[list] = None,
            datadog_logging: Optional[bool] = False,
            celery_beat: Optional[bool] = False,

            **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.task_definition = aws_ecs.TaskDefinition(
            self,
            f"{construct_id}-taskdef-{BUILD_VERSION}",
            cpu=task_definition_cpu,
            memory_mib=task_definition_memory,
            network_mode=aws_ecs.NetworkMode.AWS_VPC,
            family=construct_id,
            task_role=scope.service.task_definition.task_role,
            execution_role=scope.service.task_definition.execution_role,
            compatibility=aws_ecs.Compatibility.FARGATE,
        )
        self.repository = aws_ecr.Repository.from_repository_name(
            self,
            f"{construct_id}-repository-connection",
            repository_name=Fn.import_value(f"{PROJECT_NAME}-RepositoryName")
        )
        dd_api_secret = secretsmanager.Secret.from_secret_name_v2(
            self, f"{construct_id}-DD_API_KEY",
            secret_name="DD_API_KEY",
        )

        self.log_group = LogGroup(
            self,
            f"{construct_id}-logs",
            log_group_name=f"ecs/{construct_id}",
            removal_policy=RemovalPolicy.DESTROY,
            retention=log_retention,
        )

        environment_vars = copy(scope.service.container_environment)
        environment_vars["DD_SERVICE"] = construct_id
        self.task_definition.add_container(
            f"{construct_id}-container",
            image=aws_ecs.ContainerImage.from_ecr_repository(
                repository=self.repository,
                tag=BUILD_VERSION
            ),
            logging=aws_ecs.FireLensLogDriver(
                options={
                    "Name": "datadog",
                    "dd_service": construct_id,
                    "dd_source": "httpd",
                    "dd_version": BUILD_VERSION,
                    "dd_env": environment_name,
                    "provider": "ecs",
                    "apikey": dd_api_secret.secret_value.to_string(),
                    "Host": "http-intake.logs.datadoghq.eu",
                    "dd_message_key": "log",
                    "TLS": "on",
                }
            ),
            secrets=scope.service.secrets,
            environment=environment_vars,
            entry_point=entry_point,
            docker_labels={
                "com.datadoghq.tags.env": environment_name,
                "com.datadoghq.tags.service": construct_id,
                "com.datadoghq.tags.version": BUILD_VERSION,
            }
        )
        if celery_beat:
            self.task_definition.add_container(
                f"{construct_id}-container-beat",
                image=aws_ecs.ContainerImage.from_ecr_repository(
                    repository=self.repository,
                    tag=BUILD_VERSION
                ),
                logging=aws_ecs.FireLensLogDriver(
                    options={
                        "Name": "datadog",
                        "dd_service": f"{construct_id}-beat",
                        "dd_source": "httpd",
                        "dd_version": BUILD_VERSION,
                        "dd_env": environment_name,
                        "provider": "ecs",
                        "apikey": dd_api_secret.secret_value.to_string(),
                        "Host": "http-intake.logs.datadoghq.eu",
                        "dd_message_key": "log",
                        "TLS": "on",
                    }
                ),
                secrets=scope.service.secrets,
                environment=environment_vars,
                entry_point="celery -A freelance beat -l debug".split(),
                docker_labels={
                    "com.datadoghq.tags.env": environment_name,
                    "com.datadoghq.tags.service": f"{construct_id}-beat",
                    "com.datadoghq.tags.version": BUILD_VERSION,
                }
            )
        self.task_definition.apply_removal_policy(RemovalPolicy.RETAIN)
        aws_logs = aws_ecs.LogDriver.aws_logs(
            stream_prefix="ecs",
            log_group=self.log_group
        )
        self.task_definition.add_container(
            f"{construct_id}-datadog",
            container_name="datadog-agent",
            logging=aws_logs,
            image=aws_ecs.ContainerImage.from_registry("gcr.io/datadoghq/agent:latest"),
            port_mappings=[aws_ecs.PortMapping(container_port=8126, host_port=8126)],
            environment={
                "SD_BACKEND": "docker",
                "ECS_FARGATE": "true",
                "DD_APM_ENABLED": "true",
                "DD_SITE": "datadoghq.eu",
                "DD_APM_NON_LOCAL_TRAFFIC": "true"
            },
            secrets={"DD_API_KEY": aws_ecs.Secret.from_secrets_manager(dd_api_secret)}

        )
        if datadog_logging:
            self.task_definition.add_firelens_log_router(
                f"{construct_id}-router",
                logging=aws_logs,
                firelens_config=aws_ecs.FirelensConfig(
                    type=aws_ecs.FirelensLogRouterType.FLUENTBIT,
                    options=aws_ecs.FirelensOptions(
                        enable_ecs_log_metadata=True,
                        config_file_type=aws_ecs.FirelensConfigFileType.FILE,
                        config_file_value="/fluent-bit/configs/parse-json.conf",
                    )
                ),
                image=aws_ecs.ContainerImage.from_registry(
                    name="906394416424.dkr.ecr.ap-south-1.amazonaws.com/aws-for-fluent-bit:2.21.3"
                )
            )

        self.service = FargateService(
            self,
            id=f"{construct_id}-service",
            service_name=construct_id,
            cluster=scope.cluster,
            task_definition=self.create_dummy_task_definition(construct_id),
            platform_version=FargatePlatformVersion.VERSION1_4,
            security_groups=[scope.app_sg],
            deployment_controller=DeploymentController(type=DeploymentControllerType.ECS),
            desired_count=desired_count,
            max_healthy_percent=200,
            min_healthy_percent=100
        )

    def create_dummy_task_definition(self, construct_id: str) -> TaskDefinition:
        """
        Dummy Task Definition since updates are not supported for Blue Green deployment type
        So this part can't be changed
        """
        task_definition = TaskDefinition(
            self,
            f"{construct_id}-dummy-taskdef",
            cpu="256",
            memory_mib="512",
            network_mode=NetworkMode.AWS_VPC,
            family=construct_id,
            compatibility=Compatibility.FARGATE,
        )
        task_definition.add_container(
            f"{construct_id}-dummy-container",
            port_mappings=[PortMapping(container_port=8000, host_port=8000)],
            image=ContainerImage.from_registry(
                name="mendhak/http-https-echo:18"
            ),
            environment={"HTTP_PORT": "8000"}

        )
        return task_definition
