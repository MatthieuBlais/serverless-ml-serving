import boto3
import yaml
import uuid
import os
import datetime
import math
import json

s3 = boto3.client('s3', region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))

# os.environ["LOAD_TEST_BUCKET"] = "ml-serving-perftest"
# os.environ["ECS_CLUSTER_NAME"] = "ml-serving"
# os.environ["LOCUST_TASK_DEFINITION"] = "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/locust-load-test:3"
# os.environ["AWS_REGION"] = "ap-southeast-1"
# os.environ["CLUSTER_SUBNETS"] = "subnet-55476b32,subnet-7581dc3c"
# os.environ["CLUSTER_SECURITY_GROUPS"] = "sg-01044b90c2c0ad58e"
# os.environ["LOCUST_TASK_NAME"] = "locust-load-test"
# os.environ["LOCUST_FAMILY_NAME"] = "locust-load-test"
# os.environ["SERVING_API_HOST"] = "https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com"
# os.environ["SERVING_API_ENDPOINT"] = "/performance/"

TODAY = datetime.datetime.now().strftime("%Y-%m-%d")


def get_load_definition(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return yaml.safe_load(obj["Body"].read())


def get_rps(job):
    rps = job.get("endpoint", {}).get("rps")
    if rps is None:
        rps = event.get("InstanceTypeRPS", {}).get(job["endpoint"]["instanceType"], 10)
    if rps == 0:
        rps = 1
    return rps

def get_initial_instance_count(job):
    if job.get("endpoint", {}).get("defaultInstance"):
        return job["endpoint"]["defaultInstance"]
    rps = get_rps(job)
    return int(math.ceil(float(job['shape'][0]['users'])/float(rps)))
    
def get_scaling_policy_count(job):
    if job.get("scaling", {}).get("invocationsPerInstance"):
        return job["scaling"]["invocationsPerInstance"]
    policy = int(get_rps(job) * 60 * (1 - job["scaling"].get("safetyFactor", 0.2)))
    if job["scaling"].get("highAvailability", True):
        policy = int(policy // 2)
    return policy
    
def process_shape(test_id, job):
    shape_key = f"_loadtest/shapes/{test_id}.json"
    shape = [{
        "users": x["users"],
        "duration": x['duration'],
        "spawn_rate": x['spawnRate']
    } for x in job['shape']]
    s3.put_object(Bucket=os.environ["LOAD_TEST_BUCKET"], Key=shape_key, Body=json.dumps(shape))
    return {
        "ExpectedWorkers": math.ceil(float(max([x['users'] for x in job['shape']]))/750.0),
        "Location": {
            "Bucket": os.environ["LOAD_TEST_BUCKET"],
            "Key": shape_key
        }
    }

def format_master_command(test_id, shape_details):
    return [
      "python3",
      "driver.py",
      "--host",
      os.environ["SERVING_API_HOST"] + os.environ["SERVING_API_ENDPOINT"],
      "--client-type",
      "master",
      "--expected-workers",
      str(shape_details["ExpectedWorkers"]),
      "--master-host",
      "0.0.0.0",
      "--shapes-bucket",
      shape_details["Location"]['Bucket'],
      "--shapes-key",
      shape_details["Location"]['Key'],
      "--output-bucket",
      os.environ["LOAD_TEST_BUCKET"],
      "--output-key",
      f"_loadtesting/{TODAY}/{test_id}.json"
    ]

def format_workers(test_id, shape_details, endpoint_name, test_dataset):
    return [{
      "EndpointName": endpoint_name,
      "ExecutionId": test_id,
      "ClusterName": os.environ["ECS_CLUSTER_NAME"],
      "TaskDefinition": os.environ["LOCUST_TASK_DEFINITION"],
      "AwsRegion": os.environ["AWS_REGION"],
      "Subnets": os.environ["CLUSTER_SUBNETS"].split(","),
      "SecurityGroups": os.environ["CLUSTER_SECURITY_GROUPS"].split(","),
      "FamilyName": os.environ["LOCUST_FAMILY_NAME"],
      "TestDataset": test_dataset,
      "WorkerTaskName": os.environ["LOCUST_TASK_NAME"],
      "WorkerCommand": [
        "python3",
        "driver.py",
        "--host",
        os.environ["SERVING_API_HOST"] + os.environ["SERVING_API_ENDPOINT"],
        "--client-type",
        "worker",
        "--shapes-bucket",
        shape_details["Location"]['Bucket'],
        "--shapes-key",
        shape_details["Location"]['Key']
      ]
    } for i in range(shape_details["ExpectedWorkers"])]

def format_endpoint(event, job, counter=0):
    """Format sagemaker endpoint for load testing"""
    test_id = uuid.uuid1().hex
    instance_id = job["endpoint"]["instanceType"].replace(".", "")
    endpoint_name = "loadtesting-" + job['name'] + "-" + str(counter)
    output_result_key = f"_loadtesting/{TODAY}/{test_id}.json"
    shape_details = process_shape(test_id, job)
    test_dataset = {
        "Bucket": job["dataset"]["bucket"],
        "Key": job["dataset"]["key"]
    }
    return {
        "WaitLimit": (counter + 1)*10,
        "EndpointName": endpoint_name,
        "ModelName": event["ModelName"],
        "VariantName": "LOADTESTING",
        "InstanceType": job["endpoint"]["instanceType"],
        "InstanceCount": get_initial_instance_count(job),
        "ResultOutputs": {
            "Bucket": os.environ["LOAD_TEST_BUCKET"],
            "Key": output_result_key
        },
        "ScalingPolicy": {
            "InvocationsPerInstance": get_scaling_policy_count(job),
            "MinCapacity": job.get("scaling", {}).get("minCapacity", 2),
            "MaxCapacity": job.get("scaling", {}).get("maxCapacity", 10)
        },
        "TestDataset": test_dataset,
        "JobDetails": {
            "ExecutionId": test_id,
            "ClusterName": os.environ["ECS_CLUSTER_NAME"],
            "TaskDefinition": os.environ["LOCUST_TASK_DEFINITION"],
            "AwsRegion": os.environ["AWS_REGION"],
            "Subnets": os.environ["CLUSTER_SUBNETS"].split(","),
            "SecurityGroups": os.environ["CLUSTER_SECURITY_GROUPS"].split(","),
            "FamilyName": os.environ["LOCUST_FAMILY_NAME"],
            "MasterTaskName": os.environ["LOCUST_TASK_NAME"],
            "MasterCommand": format_master_command(test_id, shape_details)
        },
        "Jobs": format_workers(test_id, shape_details, endpoint_name, test_dataset)
    }

def handler(event, context):

    definition = get_load_definition(event["LoadJob"]["Bucket"], event["LoadJob"]["Key"])

    jobs = []
    counter = 0
    for job in definition["jobs"]:

        jobs.append(
            format_endpoint(event, job, counter)
        )
        counter += 1

    event["Jobs"] = jobs

    if "passingCriteria" in definition:
        event["PassingCriteria"] = {
            "Percentile": str(definition["passingCriteria"].get("percentile", 50)),
            "MaxResponseTime": definition["passingCriteria"].get("maxResponseTime", 100)
        }

    return event



# event = {
#     "ModelName": "tensorflow-inference-2021-03-24-13-56-47-336",
#     "LoadJob": {
#         "Bucket": "ml-serving-perftest",
#         "Key": "_loadjob/loadtest.yaml"
#     }
# }
# print(handler(event, {}))



# {
#   "EndpointName": "/dev/sentiments/tweet",
#   "TestDataset": {
#     "Bucket": "ml-serving-perftest",
#     "Key": "_data/tweet-sentiments/tweet-sentiments/dataset.csv"
#   },
#   "ResultOutputs": {
#     "Bucket": "ml-serving-perftest",
#     "Key": "_perftesting/480e30e5938c11eb82b8030ddd9037dc79b/480e30e5938c11eb82b8030ddd9037dc79b.json"
#   },
#   "JobDetails": {
#     "ExecutionId": "123",
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
#       "https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com",
#       "--client-type",
#       "master",
#       "--expected-workers",
#       "2",
#       "--master-host",
#       "0.0.0.0",
#       "--shapes-bucket",
#       "ml-serving-perftest",
#       "--shapes-key",
#       "_data/load-test/shape.json",
#       "--output-bucket",
#       "ml-serving-perftest",
#       "--output-key",
#       "_loadtesting/480e30e5938c11eb82b80309037dc79b/480e3c8d938c11eb8f610309037dc79b.json"
#     ]
#   },
#   "EndpointStatus": "InService",
#   "Jobs": [
#     {
#       "ClusterName": "ml-serving",
#       "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/locust-load-test:3",
#       "WorkerTaskName": "locust-load-test",
#       "WorkerCommand": [
#         "python3",
#         "driver.py",
#         "--host",
#         "https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com",
#         "--client-type",
#         "worker",
#         "--expected-workers",
#         "1",
#         "--master-host",
#         "10.0.2.37",
#         "--shapes-bucket",
#         "ml-serving-perftest",
#         "--shapes-key",
#         "_data/load-test/shape.json",
#         "--output-bucket",
#         "ml-serving-perftest",
#         "--output-key",
#         "_loadtesting/480e30e5938c11eb82b80309037dc79b/480e3c8d938c11eb8f610309037dc79b.json",
#         "--fargate-task",
#         "arn:aws:ecs:ap-southeast-1:908177370303:task/ml-serving/c959a8f91e2446769ffcfa8c55d721a9"
#       ],
#       "AwsRegion": "ap-southeast-1",
#       "EndpointName": "/dev/sentiments/tweet",
#       "TestDataset": {
#         "Bucket": "ml-serving-perftest",
#         "Key": "_data/tweet-sentiments/tweet-sentiments/dataset.csv"
#       },
#       "Subnets": [
#         "subnet-55476b32",
#         "subnet-7581dc3c"
#       ],
#       "SecurityGroups": [
#         "sg-01044b90c2c0ad58e"
#       ]
#     },
#     {
#       "ClusterName": "ml-serving",
#       "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/locust-load-test:3",
#       "WorkerTaskName": "locust-load-test",
#       "WorkerCommand": [
#         "python3",
#         "driver.py",
#         "--host",
#         "https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com",
#         "--client-type",
#         "worker",
#         "--expected-workers",
#         "1",
#         "--master-host",
#         "10.0.2.37",
#         "--shapes-bucket",
#         "ml-serving-perftest",
#         "--shapes-key",
#         "_data/load-test/shape.json",
#         "--output-bucket",
#         "ml-serving-perftest",
#         "--output-key",
#         "_loadtesting/480e30e5938c11eb82b80309037dc79b/480e3c8d938c11eb8f610309037dc79b.json",
#         "--fargate-task",
#         "arn:aws:ecs:ap-southeast-1:908177370303:task/ml-serving/c959a8f91e2446769ffcfa8c55d721a9"
#       ],
#       "AwsRegion": "ap-southeast-1",
#       "EndpointName": "/dev/sentiments/tweet",
#       "TestDataset": {
#         "Bucket": "ml-serving-perftest",
#         "Key": "_data/tweet-sentiments/tweet-sentiments/dataset.csv"
#       },
#       "Subnets": [
#         "subnet-55476b32",
#         "subnet-7581dc3c"
#       ],
#       "SecurityGroups": [
#         "sg-01044b90c2c0ad58e"
#       ]
#     }
#   ]
# }