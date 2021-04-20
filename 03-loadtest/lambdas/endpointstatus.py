import boto3
import json

sagemaker = boto3.client("sagemaker")

def handler(event, context):

    print(json.dumps(event))

    endpoint = sagemaker.describe_endpoint(EndpointName=event["EndpointName"])

    if endpoint["EndpointStatus"] in ["OutOfService", "Failed"]:
        sagemaker.delete_endpoint(EndpointName=event["EndpointName"])
        sagemaker.delete_endpoint_config(EndpointConfigName=event["EndpointName"])
        raise Exception("Endpoint failed to create")

    event["EndpointStatus"] = endpoint["EndpointStatus"]

    return event