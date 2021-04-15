import boto3
import os
import uuid

asc = boto3.client('application-autoscaling', region_name=os.environ["AWS_REGION"])

def handler(event, context):

    invocations_per_instance = event["ScalingPolicy"]["InvocationsPerInstance"] * 60

    policy = {
        "TargetValue": invocations_per_instance,
        "PredefinedMetricSpecification":
        {
            "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
        }
    }

    policy_name = uuid.uuid1().hex
    response = asc.put_scaling_policy(
        PolicyName=policy_name,
        ServiceNamespace='sagemaker',
        ResourceId=f'endpoint/{event["EndpointName"]}/variant/{event["VariantName"]}',
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        TargetTrackingScalingPolicyConfiguration=policy
    )

    event["ScalingPolicy"]["PolicyName"] = policy_name

    return event