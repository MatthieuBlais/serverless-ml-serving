import boto3
import os
import uuid

asc = boto3.client('application-autoscaling', region_name=os.environ["AWS_REGION"])

def handler(event, context):

    asc.register_scalable_target(
        ServiceNamespace='sagemaker',
        ResourceId=f'endpoint/{event["EndpointName"]}/variant/{event["VariantName"]}',
        ScalableDimension='sagemaker:variant:DesiredInstanceCount',
        MinCapacity=event.get("ScalingPolicy", {}).get("MinCapacity", 2),
        MaxCapacity=event.get("ScalingPolicy", {}).get("MaxCapacity", 10)
    )

    policy = {
        "TargetValue": event["ScalingPolicy"]["InvocationsPerInstance"],
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
        PolicyType="TargetTrackingScaling",
        TargetTrackingScalingPolicyConfiguration=policy
    )

    event["ScalingPolicy"]["PolicyName"] = policy_name

    return event



# event = {
#   "WaitLimit": 10,
#   "EndpointName": "loadtesting-dddd-0",
#   "ModelName": "tensorflow-inference-2021-03-24-13-56-47-336",
#   "VariantName": "LOADTESTING",
#   "InstanceType": "ml.c4.xlarge",
#   "InstanceCount": 2,
#   "ResultOutputs": {
#     "Bucket": "ml-serving-perftest",
#     "Key": "_loadtesting/fe06e176a1a811eb9f6cebfbfff741be/fe06ee38a1a811eb9d55ebfbfff741be.json"
#   },
#   "ScalingPolicy": {
#     "InvocationsPerInstance": 240
#   },
#   "TestDataset": {
#     "Bucket": "ml-serving-perftest",
#     "Key": "_data/tweet-sentiments/tweet-sentiments/dataset.csv"
#   },
#   "JobDetails": {
#     "ExecutionId": "fe06e176a1a811eb9f6cebfbfff741be",
#     "ClusterName": "ml-serving",
#     "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/locust-load-test:3",
#     "AwsRegion": "ap-southeast-1",
#     "Subnets": [
#       "subnet-55476b32",
#       "subnet-7581dc3c"
#     ],
#     "SecurityGroups": [
#       "sg-01044b90c2c0ad58e"
#     ],
#     "FamilyName": "locust-load-test",
#     "MasterTaskName": "locust-load-test",
#     "MasterCommand": [
#       "python3",
#       "driver.py",
#       "--host",
#       "https://zgr57hqpad.execute-api.ap-southeast-1.amazonaws.com/api/performance/",
#       "--client-type",
#       "master",
#       "--expected-workers",
#       "1",
#       "--master-host",
#       "0.0.0.0",
#       "--shapes-bucket",
#       "ml-serving-perftest",
#       "--shapes-key",
#       "_loadtest/shapes/fe06e176a1a811eb9f6cebfbfff741be.json",
#       "--output-bucket",
#       "ml-serving-perftest",
#       "--output-key",
#       "_loadtesting/2021-04-20/fe06e176a1a811eb9f6cebfbfff741be.json"
#     ]
#   },
#   "Jobs": [
#     {
#       "EndpointName": "loadtesting-dddd-0",
#       "ExecutionId": "fe06e176a1a811eb9f6cebfbfff741be",
#       "ClusterName": "ml-serving",
#       "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/locust-load-test:3",
#       "AwsRegion": "ap-southeast-1",
#       "Subnets": [
#         "subnet-55476b32",
#         "subnet-7581dc3c"
#       ],
#       "SecurityGroups": [
#         "sg-01044b90c2c0ad58e"
#       ],
#       "FamilyName": "locust-load-test",
#       "TestDataset": {
#         "Bucket": "ml-serving-perftest",
#         "Key": "_data/tweet-sentiments/tweet-sentiments/dataset.csv"
#       },
#       "WorkerCommand": [
#         "python3",
#         "driver.py",
#         "--host",
#         "https://zgr57hqpad.execute-api.ap-southeast-1.amazonaws.com/api/performance/",
#         "--client-type",
#         "worker",
#         "--shapes-bucket",
#         "ml-serving-perftest",
#         "--shapes-key",
#         "_loadtest/shapes/fe06e176a1a811eb9f6cebfbfff741be.json"
#       ]
#     }
#   ],
#   "EndpointStatus": "InService"
# }
# handler(event, {})