import boto3
import json

s3 = boto3.client("s3")

def format_output(event, instance_details, results):
    if "Percentiles" not in event:
        return {
            "instance": instance_details,
            "performance": results
        }
    formatted = []
    results = [results]
    for r in results:
        item = {
            "current_rps": r["current_rps"],
            "current_fail_per_sec": r["current_fail_per_sec"],
            "user_count": r["user_count"],
            "num_requests": r["num_requests"]
        }
        for percentile in event["Percentiles"]:
            if f"response_time_percentile_{percentile}" in r:
                item[f"response_time_percentile_{percentile}"] = r[f"response_time_percentile_{percentile}"]
        formatted.append(item)
    
    return {
            "instance": {
                "instanceName": instance_details["instanceName"],
                "vCpu": instance_details["vCpu"],
                "memory": instance_details["memory"],
                "gpu": instance_details["gpu"],
                "onDemandUsdPrice": instance_details["onDemandUsdPrice"],
                "monthlyEstimate": instance_details["onDemandUsdPrice"] * 24 * 30
            },
            "performance": formatted
        }

def read_job_results(event):
    """Read Locust results from S3"""
    out = []
    for job in event["Jobs"]:
        obj = s3.get_object(Bucket=job["ResultOutputs"]["Bucket"], Key=job["ResultOutputs"]["Key"])
        result = json.loads(obj['Body'].read())
        out.append(format_output(event, job['InstanceDetails'], result))
    sorting_key = f'response_time_percentile_{min(event.get("Percentiles", [75]))}'
    return sorted(out, key=lambda x: (sorting_key, x['instance']['onDemandUsdPrice']))
    

def handler(event, context):

    print(json.dumps(event))

    results = read_job_results(event)

    print(results)

    return results