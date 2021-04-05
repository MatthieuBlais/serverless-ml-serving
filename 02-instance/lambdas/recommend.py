import boto3
import json
import matplotlib.pyplot as plt
from io import BytesIO

s3 = boto3.client("s3")


def get_recommendation(event, results):
    if "PassingCriteria" not in event:
        return None
    criteria = event["PassingCriteria"]
    if "Users" not in criteria or "MaxResponseTime" not in criteria:
        return results[0]
    percentile = criteria.get("Percentile", min([int(key.split("_")[-1]) for key in results[0]["performance"][0] if key.startswith("response_time_percentile_")]))
    for instance_type in results:
        for perf in instance_type['performance']:
            if (
                perf['user_count'] >= criteria['Users']
                and f"response_time_percentile_{percentile}" in perf
                and perf[f"response_time_percentile_{percentile}"] <= criteria["MaxResponseTime"]
            ):
                return instance_type
    return None

def generate_series(instance_name, results):
    percentiles = [key for key in results[0].keys() if key.startswith("response_time_percentile_")]
    percentiles = sorted(percentiles, key=lambda x: int(x.split("_")[-1]))
    if len(percentiles) > 2:
        percentiles = percentiles[:2]
    x = [r['user_count'] for r in results]
    for key in percentiles:
        y = [r[key] for r in results]
        plt.plot(x, y, label = instance_name + f"(p{key.split('_')[-1]})")
        

def generate_matplotlib():
    plt.xlabel('active users')
    plt.ylabel('response time (ms)')
    plt.title('Performance testing')
    plt.legend()
    img_data = BytesIO()
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    return img_data

def format_output(event, instance_details, results):
    if "Percentiles" not in event:
        return {
            "instance": instance_details,
            "performance": results
        }
    formatted = []
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
    plt.figure(figsize=(15, 15))
    for job in event["Jobs"]:
        obj = s3.get_object(Bucket=job["ResultOutputs"]["Bucket"], Key=job["ResultOutputs"]["Key"])
        result = json.loads(obj['Body'].read())
        out.append(format_output(event, job['InstanceDetails'], result))
        generate_series(job['InstanceDetails']['instanceName'], result)
    sorting_key = f'response_time_percentile_{min(event.get("Percentiles", [75]))}'
    plot = generate_matplotlib()
    return sorted(out, key=lambda x: (sorting_key, x['instance']['onDemandUsdPrice'])), plot
    
def save_s3(jobs, results, plot):
    perftest_prefix = "/".join(jobs[0]['ResultOutputs']['Key'].split("/")[:-1])
    perftest_bucket = jobs[0]['ResultOutputs']['Bucket']
    s3.put_object(Bucket=perftest_bucket, Key=perftest_prefix+"/perftest_results.json", Body=json.dumps(results))
    s3.put_object(Bucket=perftest_bucket, Key=perftest_prefix+"/perftest_results.png", Body=plot, ContentType='image/png')
    return (
        f"s3://{perftest_bucket}/{perftest_prefix+'/perftest_results.json'}",
        f"s3://{perftest_bucket}/{perftest_prefix+'/perftest_results.png'}"
    )


def handler(event, context):

    print(json.dumps(event))

    results, plot = read_job_results(event)
    recommendation = get_recommendation(event, results)
    result_json, result_png = save_s3(event["Jobs"], results, plot)

    results = {
        "recommendation": recommendation,
        "result_path": result_json,
        "result_png": result_png,
        "stats": results
    }

    print(results)

    return results