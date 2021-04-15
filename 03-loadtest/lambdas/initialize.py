import boto3
import yaml
import uuid

s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])

def get_load_definition(bucket, key):
    obj = s3.read_object(Bucket=bucket, Key=key)
    return yaml.safe_load(obj["Body"].read())

def format_endpoint(event, job, counter=0):
    """Format sagemaker endpoint for load testing"""
    test_id = uuid.uuid1().hex
    instance_id = job["endpoint"]["instanceType"].replace(".", "")
    endpoint_name = "loadtesting-" + instance_id + "-" + event.get("EndpointName", event["ModelName"])
    output_result_key = "_loadtesting/" + test_id + "/" + uuid.uuid1().hex + ".json"
    return {
        "WaitLimit": (counter + 1)*10,
        "EndpointName": endpoint_name,
        "ModelName": event["ModelName"],
        "VariantName": "LOADTESTING",
        "InstanceType": job["endpoint"]["instanceType"],
        "InitialInstanceCount": job["endpoint"].get("defaultInstance", 1),
        "ResultOutputs": {
            "Bucket": os.environ["LOAD_TEST_BUCKET"],
            "Key": output_result_key
        },
        "ScalingPolicy": {
            "InvocationsPerInstance": job["endpoint"]["rps"] * job["endpoint"].get("safetyFactor", int(job["endpoint"]["rps"]*0.2))
        },
        "TestDataset": event["TestDataset"],
        "JobDetails": {
            "ClusterName": os.environ["ECS_CLUSTER_NAME"],
            "TaskDefinition": os.environ["LOCUST_TASK_DEFINITION"],
            "AwsRegion": os.environ["AWS_REGION"],
            "Subnets": os.environ["CLUSTER_SUBNETS"].split(","),
            "TaskName": os.environ["LOCUST_TASK_NAME"],
            "Command": f"python3 driver.py -t {test_time} -H {host} --output-bucket {os.environ['PERF_TEST_BUCKET']} --output-key {output_result_key} --percentiles {percentiles}".split(" ")
        }
    }

def hendler(event, context):

    definition = get_load_definition(event["Bucket"], event["Key"])

    jobs = []
    counter = 0
    for job in definition["jobs"]:

        usecases.append(
            format_endpoint(event, job, counter)
        )
        counter += 1

    event["Jobs"] = usecases

    return event