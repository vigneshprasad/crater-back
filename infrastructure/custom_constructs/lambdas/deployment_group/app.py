import logging
from typing import List, Optional

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEPLOYMENT_STYLE = {
    "deploymentType": "BLUE_GREEN",
    "deploymentOption": "WITH_TRAFFIC_CONTROL"
}


def create_deployment_group(
        deployment_group_name: str,
        cluster_name: str,
        service_name: str,
        application_name: str,
        target_group_names: List[str],
        prod_traffic_listener_arn: str,
        test_traffic_listener_arn: str,
        service_role_arn: str,
        wait_time: Optional[int] = 5,
        **kwargs
) -> dict:
    response = boto3.client("codedeploy").create_deployment_group(
        applicationName=application_name,
        deploymentGroupName=deployment_group_name,
        ecsServices=[{"serviceName": service_name, "clusterName": cluster_name}],
        serviceRoleArn=service_role_arn,
        autoRollbackConfiguration={
            "enabled": True,
            "events": [
                "DEPLOYMENT_FAILURE"
            ]
        },
        deploymentStyle=DEPLOYMENT_STYLE,
        blueGreenDeploymentConfiguration={
            "terminateBlueInstancesOnDeploymentSuccess": {
                "action": "TERMINATE",
                "terminationWaitTimeInMinutes": int(wait_time)
            },
            "deploymentReadyOption": {
                "actionOnTimeout": "CONTINUE_DEPLOYMENT",
            }

        },
        loadBalancerInfo={
            "targetGroupPairInfoList": [
                {
                    "targetGroups": [{"name": name} for name in target_group_names],
                    "prodTrafficRoute": {
                        "listenerArns": [prod_traffic_listener_arn]
                    },
                    "testTrafficRoute": {
                        "listenerArns": [test_traffic_listener_arn]
                    }
                },
            ]
        },
    )
    logger.info(response)
    return {"deploymentGroupId": deployment_group_name}


def update_deployment_group(
        deployment_group_name: str,
        old_deployment_group_name: str,
        cluster_name: str,
        service_name: str,
        application_name: str,
        target_group_names: List[str],
        prod_traffic_listener_arn: str,
        test_traffic_listener_arn: str,
        service_role_arn: str,
        wait_time: Optional[int] = 5,
        **kwargs
) -> dict:
    """ Command used for Deployment group creation after Code Deploy application is created """
    response = boto3.client("codedeploy").update_deployment_group(
        applicationName=application_name,
        currentDeploymentGroupName=old_deployment_group_name,
        newDeploymentGroupName=deployment_group_name,
        ecsServices=[{"serviceName": service_name, "clusterName": cluster_name}],
        serviceRoleArn=service_role_arn,
        autoRollbackConfiguration={
            "enabled": True,
            "events": [
                "DEPLOYMENT_FAILURE"
            ]
        },
        deploymentStyle=DEPLOYMENT_STYLE,
        blueGreenDeploymentConfiguration={
            "terminateBlueInstancesOnDeploymentSuccess": {
                "action": "TERMINATE",
                "terminationWaitTimeInMinutes": int(wait_time)
            },
            "deploymentReadyOption": {
                "actionOnTimeout": "CONTINUE_DEPLOYMENT",
            }
        },
        loadBalancerInfo={
            "targetGroupPairInfoList": [
                {
                    "targetGroups": [{"name": name} for name in target_group_names],
                    "prodTrafficRoute": {
                        "listenerArns": [prod_traffic_listener_arn]
                    },
                    "testTrafficRoute": {
                        "listenerArns": [test_traffic_listener_arn]
                    }
                },
            ]
        },
    )
    logger.info(response)
    return {"deploymentGroupId": deployment_group_name}


def delete_deployment_group(deployment_group_name: str, application_name: str, **kwargs):
    response = boto3.client("codedeploy").delete_deployment_group(
        applicationName=application_name,
        deploymentGroupName=deployment_group_name,
    )
    logger.info(response)


def handler(event, context):
    mapping = {
        "Create": create_deployment_group,
        "Update": update_deployment_group,
        "Delete": delete_deployment_group
    }
    response = mapping[event["RequestType"]](
        **event["ResourceProperties"],
        old_deployment_group_name=event.get("OldResourceProperties", {}).get("deployment_group_name")
    )
    return response
