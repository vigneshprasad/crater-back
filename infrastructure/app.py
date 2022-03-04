#!/usr/bin/env python3
import os

import aws_cdk as cdk

from conf import ACCOUNT, DEV_ENV, PROD_ENV, PROJECT_NAME, REGION
from stacks.ecr import ECRStack
from stacksets.base import BackendStack


app = cdk.App()


repository_stack = ECRStack(app, PROJECT_NAME, env=cdk.Environment(account=ACCOUNT, region=REGION))
BackendStack(
    app,
    f"{PROJECT_NAME}-api-dev",
    env=DEV_ENV,
)

BackendStack(
    app,
    f"{PROJECT_NAME}-api-prod",
    env=PROD_ENV,
)

app.synth()

