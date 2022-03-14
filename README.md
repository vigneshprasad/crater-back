# Backend

## Stack

- Python 3.8
- Django
- Celery
- Uvicorn
- Redis
- PostgreSQL

## Get started

### Local setup

Start local dev server:

```sh
pip install -r requirements.txt
./bin/develop.sh
```

### Docker setup

Get latest docker & docker-compose:

- https://www.docker.com/
- https://docs.docker.com/compose/

```sh
docker-compose up -d
```

Wait for docker to set up containers, then open [http://localhost:8000](http://localhost:8000)

## AWS CLI

AWS CLI is needed to

- Login to AWS ECR repository
- Deploy CDK stacks
- Retrieve secrets from AWS secrets manager

[AWS CLI Installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

[AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)

# CDK AWS infrastructure

CDK installation

```bash
sudo npm install -g aws-cdk@latest
```

Python dependencies can be installed via **pip** or **piptools**

```bash
pip install -r infrastructure/requirements.txt
```

- [CDK applications files](infrastructure/app.py)
    - worknetwork-api - Stack with ECR repository which is used in prod and dev stacks
    - worknetwork-api-prod - Production environment resources stack
    - worknetwork-api-dev - Development environment resources stack
- [CDK stacks environment configurations and settings](infrastructure/conf.py)
- [Main infrastructure stack](infrastructure/stacksets/base.py) - File where nested stacks are used and whole
  infrastructure components are connected
- [Nested stacks](infrastructure/stacks/stacks) - Seperate nested stacks, used to group needed resources per service (
  DB, ALB, ECS...)

## Useful commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

```bash
cdk diff worknetwork-api-dev - # Shows what changes would be made if stack would be deployed
cdk delploy worknetwork-api-dev - # Stars development stack deployment
```

If stacks fail to deploy and console does not show proper error message
Exploring [Cloudformation console](https://ap-south-1.console.aws.amazon.com/cloudformation/)  during redeployment of
the stack can help

- [CDK API References](https://docs.aws.amazon.com/cdk/api/v2/python/index.html)
- [CDK Developers guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html)

# Infrastructure

![deploy](infrastructure.png)

[Link to edit](https://lucid.app/lucidchart/902bc797-1bf9-416d-a671-f8e92649ffc9/edit?invitationId=inv_f6767c0d-1cbc-4248-b896-40c275cabecb)
.

### [VPC](https://ap-south-1.console.aws.amazon.com/vpc/home?region=ap-south-1#vpcs:)

- Private Subnets (Not reachable from outside internet, ECS containers, RDS databases, Cache instances)
- Public Subnets (Not reachable from outside internet (Load balancers, Bastion host, NAT gateways/instances))
- NAT instances to allow internet access from private subnets
    - For cost savings it is enabled in only one AZ
- Bastion host to enable access to VPC

[More on AWS Virtual private cloud](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)

### [Load balancer](https://ap-south-1.console.aws.amazon.com/ec2/v2/home?region=ap-south-1#LoadBalancers:sort=loadBalancerName)

- Application Load balancers which forward traffic and monitor ECS services
- SSL Certificates are taken from ACM
- Port 433 Main traffic listener
- Port 8433 Test traffic listener
- Port 80(HTTP) Redirect to 433 (HTTPS)

[Target Groups](https://ap-south-1.console.aws.amazon.com/ec2/v2/home?region=ap-south-1#TargetGroups:)

- Blue target group
- Green target group

[More on Elastic Load Balancing](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html)

### [Databases](https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1#databases:)

- [PostgreSQL for Dev](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [Aurora PostgreSQL for Prod](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/CHAP_AuroraOverview.html)

### [Elastic container service ](https://ap-south-1.console.aws.amazon.com/ecs/home?region=ap-south-1#/clusters)

**Django** service consists of

- **Django** application running on Uvicorn server
- **Datadog agent** - Application and container metrics collector shipper to Datadog site
- **FluentBit** Logs shipper to Datadog site

**Celery** service consists of:
- **Celery** worker - Celery task executor
- **Celery Beat** worker - Celery task scheduler
- **Datadog agent** 
- **FluentBit** 

Resources:

- [Dev Cluster](https://ap-south-1.console.aws.amazon.com/ecs/home?region=ap-south-1#/clusters/worknetwork-api-dev-cluster/services)
- [Prod Cluster](https://ap-south-1.console.aws.amazon.com/ecs/home?region=ap-south-1#/clusters/worknetwork-api-prod-cluster/services)
- [Container parameters](https://ap-south-1.console.aws.amazon.com/systems-manager/parameters/?region=ap-south-1&tab=Table)
- [Container secrets](https://ap-south-1.console.aws.amazon.com/secretsmanager/home?region=ap-south-1#!/listSecrets/)

[More on ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)

### Cache

- [ElastiCache for Redis](https://ap-south-1.console.aws.amazon.com/elasticache/home?region=ap-south-1#redis:)

### DNS

Domain is registered in NameCheap, but it is using AWS Nameservers

- [Route53](https://ap-south-1.console.aws.amazon.com/route53/v2/hostedzones#)
- [SSL Certificates](https://ap-south-1.console.aws.amazon.com/acm/home?region=ap-south-1#/certificates/list)

### Certificates
- Certificates are created and stored in [AWS Certificate Manager (ACM)](https://ap-south-1.console.aws.amazon.com/acm/home?region=ap-south-1#/certificates/list)
- Certificates for Cloudfront have to be created in **us-east-1** region
### CDN
Cloudfront is used cache responses from Django application. Origin is set to Application Load balancer.
- [Dev distribution](https://us-east-1.console.aws.amazon.com/cloudfront/v3/home?region=ap-south-1#/distributions/E3JM6EI50YBEE3)
- [Prod distribution](https://us-east-1.console.aws.amazon.com/cloudfront/v3/home?region=ap-south-1#/distributions/E180SGZQFFNT2N)

[More on Cloudfront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html)

### [S3 buckets](https://s3.console.aws.amazon.com/s3/home?region=ap-south-1#)

- Media uploads bucket - Uploads from django application with public/private object acls
- Static files buckets - Bucket with public read access to serve django static files

## [CodeDeploy](https://ap-south-1.console.aws.amazon.com/codesuite/codedeploy/applications?region=ap-south-1)

- For ECS service
  deployment [Blue Green Deployment](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html)
  is used

[More on AWS CodeDeploy](https://docs.aws.amazon.com/codedeploy/latest/userguide/welcome.html)

### Gitlab Pipelines

[CI file](.gitlab-ci.yml)

- Requirements check - Checking if requirements.txt and Dockerfile changed. If so, rebuild base images
- Building - Building main Application image with Base images from Requirements check step
- Testing - Checking AWS CDK changes
- Deploy infrastructure - Deploying AWS CDK (if nothing is changed, new task definition with changed image tag is deployed)
- Deploy Django app - Deploying new task definition to Django Service
- Deploy Celery app - Deploying new task definition to Celery Service

### Manual Image building and pushing to ECR

Retrieve an authentication token and authenticate your Docker client to your registry. Use the AWS CLI:

```bash
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 682452685130.dkr.ecr.ap-south-1.amazonaws.com
```

Build your Docker image using the following command. For information on building a Docker file from scratch see the
instructions here . You can skip this step if your image is already built:

```bash
docker build -t 682452685130.dkr.ecr.ap-south.amazonaws.com/worknetwork:latest .
```

Run the following command to push this image to your newly created AWS repository:

```bash
docker push 682452685130.dkr.ecr.ap-south.amazonaws.com/worknetwork:latest
```


# Load Testing

Locust is used for load testing

Quickstart
```bash
pip install locust
locust
```
Endpoinds to test are create in [locustfile](locustfile.py)

[More on locust](http://docs.locust.io/en/stable/)
