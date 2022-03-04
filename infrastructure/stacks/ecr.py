import jsii
from aws_cdk import CfnOutput, ITaggable, RemovalPolicy, Stack
from aws_cdk.aws_ecr import Repository
from constructs import Construct


@jsii.implements(ITaggable)
class ECRStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.repository = Repository(
            self,
            construct_id,
            repository_name=construct_id,
            removal_policy=RemovalPolicy.DESTROY
        )
        self.repository_uri = CfnOutput(
            self,
            f"{construct_id}-RepositoryURI",
            export_name=f"{construct_id}-RepoURI",
            value=self.repository.repository_uri
        )
        self.repository_name = CfnOutput(
            self,
            f"{construct_id}-RepositoryName",
            export_name=f"{construct_id}-RepositoryName",
            value=self.repository.repository_name
        )
