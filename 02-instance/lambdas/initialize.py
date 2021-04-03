from pricing import SagemakerProducts
from pricing import InstanceFilter
import os
import uuid
import json


LOCATION = os.environ.get("PRICING_LOCATION", "Asia Pacific (Singapore)")

def fetch_instances(event):
    """Fetch SageMaker Instances and filter them to meet event criteria"""
    instances = SagemakerProducts.fetch(LOCATION)
    event_filters = event.get("Filters", {})
    filters = {
        'products': instances,
        'min_vcpu': event_filters.get("MinCPU", 0), 
        'max_vcpu': event_filters.get("MaxCPU", float("inf")), 
        'min_memory': event_filters.get("MinMemory", 0), 
        'max_memory': event_filters.get("MaxCPU", float("inf")),
        'min_gpu': event_filters.get("MinGPU", 0), 
        'max_gpu': event_filters.get("MaxGPU", float("inf")),
        'min_usd': event_filters.get("MinUSD", 0), 
        'max_usd': event_filters.get("MaxUSD", float("inf")),
        'instance_types': event_filters.get("InstanceTypes", []),
        'max_instance_types': event_filters.get("MaxInstances", 5)
    }
    return InstanceFilter.apply(**filters)


def format_endpoints(event, instances):
    """Format test jobs for the few selected instances"""
    jobs = []
    test_id = uuid.uuid1().hex
    counter = 0
    for instance in instances:
        instance_id = instance['instanceName'].replace(".", "")
        endpoint_name = "perf-" + instance_id + "-" + event.get("EndpointName", event["ModelName"])
        output_result_key = "_perftesting/" + test_id + "/" + uuid.uuid1().hex + ".json"
        jobs.append({
            "WaitLimit": (counter + 1)*10,
            "EndpointName": endpoint_name,
            "ModelName": event["ModelName"],
            "VariantName": "ALLVARIANT",
            "InstanceDetails": instance,
            "ResultOutputs": {
                "Bucket": os.environ["PERF_TEST_BUCKET"],
                "Key": output_result_key
            },
            "PerfSettings": format_jobs(event, endpoint_name, output_result_key)
        })
        counter += 1
    return jobs

def format_jobs(event, endpoint_name, output_result_key):
    host = os.environ["SERVING_API_HOST"] + os.environ["SERVING_API_ENDPOINT"]
    jobs = []
    for settings in event.get("Settings", [{}]):
        users = settings.get("Users", 5)
        spawn_rate = settings.get("SpawnRate", 5)
        test_time = settings.get("TestTime", 300)
        jobs.append({
            "EndpointName": endpoint_name,
            "TestDataset": event["TestDataset"],
            "ResultOutputs": {
                "Bucket": os.environ["PERF_TEST_BUCKET"],
                "Key": output_result_key
            },
            "JobDetails": {
                "ClusterName": os.environ["ECS_CLUSTER_NAME"],
                "TaskDefinition": os.environ["LOCUST_TASK_DEFINITION"],
                "AwsRegion": os.environ["AWS_REGION"],
                "Subnets": os.environ["CLUSTER_SUBNETS"].split(","),
                "TaskName": os.environ["LOCUST_TASK_NAME"],
                "Command": f"python3 driver.py -u {users} -r {spawn_rate} -t {test_time} -H {host} --output-bucket {os.environ['PERF_TEST_BUCKET']} --output-key {output_result_key}".split(" ")
            }
        })

    return jobs

def handler(event, context):
    print(json.dumps(event))

    instances = fetch_instances(event)
    jobs = format_endpoints(event, instances)

    event["Jobs"] = jobs

    print(json.dumps(event))

    return event

