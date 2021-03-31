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


def format_jobs(event, instances):
    """Format test jobs for the few selected instances"""
    jobs = []
    test_id = uuid.uuid1().hex
    for instance in instances:
        instance_id = instance['instanceName'].replace(".", "")
        jobs.append({
            "EndpointName": instance_id + "-" + event.get("EndpointName", event["ModelName"]),
            "ModelName": event["ModelName"],
            "VariantName": "ALLVARIANT",
            "InstanceDetails": instance,
            "TestDataset": event["TestDataset"],
            "ResultOutputs": {
                "Bucket": os.environ[""],
                "Key": "_perftesting/" + test_id + "/" + uuid.uuid1().hex + ".json"
            },
            "JobDetails": {
                "ClusterName": os.environ["ECS_CLUSTER_NAME"],
                "TaskDefinition": os.environ["LOCUST_TASK_DEFINITION"]
            }
        })
    return jobs


def handler(event, context):
    print(json.dumps(event))

    instances = fetch_instances(event)
    jobs = format_jobs(event, instances)

    event["Jobs"] = jobs

    print(json.dumps(event))

    return event
