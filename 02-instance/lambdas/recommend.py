import boto3
import json

s3 = boto3.client("s3")

def read_job_results(jobs):
    """Read Locust results from S3"""
    out = []
    for job in jobs:
        obj = s3.get_object(Bucket=job["ResultOutputs"]["Bucket"], Key=job["ResultOutputs"]["Key"])
        result = json.loads(obj['Body'].read())
        result["instance"] = job['InstanceDetails']
        out.append(result)
    return out

def handler(event, context):

    print(json.dumps(event))

    results = read_job_results(jobs)

    print(results)

    return results