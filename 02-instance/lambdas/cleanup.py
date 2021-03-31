import boto3
import json

sagemaker = boto3.client("sagemaker")

def handler(event, context):

    print(json.dumps(event))

    sagemaker.delete_endpoint(EndpointName=event["EndpointName"])
    sagemaker.delete_endpoint_config(EndpointConfigName=event["EndpointName"])

    return event