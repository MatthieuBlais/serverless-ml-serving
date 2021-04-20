import boto3
import json
import os

sagemaker = boto3.client("sagemaker", region_name=os.environ["AWS_REGION"])
asc = boto3.client('application-autoscaling', region_name=os.environ["AWS_REGION"])

def handler(event, context):

    print(json.dumps(event))

    sagemaker.delete_endpoint(EndpointName=event["EndpointName"])
    sagemaker.delete_endpoint_config(EndpointConfigName=event["EndpointName"])
    asc.delete_scaling_policy(
        PolicyName=event["ScalingPolicy"]["PolicyName"],
        ServiceNamespace="sagemaker",
        ResourceId=f'endpoint/{event["EndpointName"]}/variant/{event["VariantName"]}',
        ScalableDimension="sagemaker:variant:DesiredInstanceCount"
    )
    asc.deregister_scalable_target(
        ServiceNamespace='sagemaker',
        ResourceId=f'endpoint/{event["EndpointName"]}/variant/{event["VariantName"]}',
        ScalableDimension='sagemaker:variant:DesiredInstanceCount'
    )

    return event

