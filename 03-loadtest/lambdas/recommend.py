import json
import boto3
import os
from graph import Graph


s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))



def download_results(result_output):
    obj = s3.get_object(Bucket=result_output["Bucket"], Key=result_output["Key"])
    return json.loads(obj['Body'].read())

def extract_overall_stats(job_result):
    out = {
        "MinResponseTime": job_result["min_response_time"],
        "MaxResponseTime": job_result["max_response_time"],
        "NumRequests": job_result["num_requests"]
    }
    for key in job_result.keys():
        if key.startswith("response_time_percentile"):
            out["".join([x.title() for x in key.split("_")])] = job_result[key]
    return out

def avg(arr):
    return round(float(sum(arr))/float(len(arr)),2)

def get_details_summary(arr):
    return {
        "Min": min(arr),
        "Max": max(arr),
        "Avg": avg(arr)
    }

def get_graph(series, labels, bucket, key):
    return Graph.generate_graph(labels, series, bucket, key)

def extract_details(job_result, bucket, prefix):
    mem = {}
    for stats in job_result["history"]:
        if stats["user_count"] not in mem:
            mem[stats["user_count"]] = []
        mem[stats["user_count"]].append(stats)
    out = []
    for key, val in mem.items():
        details = {
            "Users": key,
            "Duration": len(val)*5,
            "RequestPerSec": get_details_summary([x["current_rps"] for x in val]),
            "FailPerSec": get_details_summary([x["current_fail_per_sec"] for x in val])
        }
        series = []
        labels = []
        for k in val[0].keys():
            if k.startswith("response_time_percentile"):
                details["".join([x.title() for x in k.split("_")])] = get_details_summary(
                    [x[k] for x in val], 
                )
                series.append([x[k] for x in val])
                labels.append(k)

        details["Graph"] = get_graph(series, labels, bucket, prefix + str(key) + ".png")
        
        out.append(details)
    return out


def format_results(job_details, job_result):
    output_bucket = job_details["ResultOutputs"]["Bucket"]
    output_prefix = job_details["ResultOutputs"]["Key"].split(".")[0] + "/" + job_details["EndpointName"] + "/"
    series = []
    labels = []
    users = []
    users.append([x['current_rps'] for x in job_result['history']])
    for k in job_result.keys():
        if k.startswith("response_time_percentile"):
            series.append([x[k] for x in job_result['history']])
            labels.append(k)
    return {
        "InstanceType": job_details["InstanceType"],
        "InstanceCount": job_details["InstanceCount"],
        "ScalingPolicy": job_details["ScalingPolicy"],
        "Statistics": extract_overall_stats(job_result),
        "Details": extract_details(job_result, output_bucket, output_prefix),
        "ResponseTimeGraph": get_graph(series, labels, output_bucket, output_prefix + "response-time.png"),
        "UserGraph": get_graph(users, ["rps"], output_bucket, output_prefix + "user-time.png")
    }


def get_recommendation(jobs, criteria):
    if "Percentile" not in criteria:
        criteria["Percentile"] = "50"
    passing = []
    for job in jobs:
        if job["Statistics"].get(f"ResponseTimePercentile{criteria['Percentile']}", float("inf")) <= criteria["MaxResponseTime"]:
            passing.append(job)
    return {
        "Passed": len(passing) > 0,
        "Configurations": passing,
    }


def handler(event, context):

    print(json.dumps(event))

    output = {
        "Details": []
    }

    if len(event["Jobs"]) == 0:
        return {
            "Recommendation": "No job"
        }

    results = download_results(event["Jobs"][0]["ResultOutputs"])
    
    for idx, job in enumerate(event["Jobs"]):

        results = download_results(job["ResultOutputs"])
        # print(results[0].keys())
        # print(json.dumps(results, indent=4))
        output["Details"].append(format_results(job, results[idx]))
        
    if "PassingCriteria" in event:
        output["Recommendation"] = get_recommendation(output["Details"], event["PassingCriteria"])

    return output



# event = {
#   "ModelName": "tensorflow-inference-2021-03-24-13-56-47-336",
#   "LoadJob": {
#     "Bucket": "ml-serving-perftest",
#     "Key": "_loadjob/loadtest.yaml"
#   },
#   "PassingCriteria": {
#       "Percentile": 50,
#       "MaxResponseTime": 100
#   },
#   "Jobs": [
#     {
#       "WaitLimit": 10,
#       "EndpointName": "loadtesting-dddd-0",
#       "ModelName": "tensorflow-inference-2021-03-24-13-56-47-336",
#       "VariantName": "LOADTESTING",
#       "InstanceType": "ml.c4.xlarge",
#       "InstanceCount": 2,
#       "ResultOutputs": {
#         "Bucket": "ml-serving-perftest",
#         "Key": "_loadtesting/2021-04-20/bd0e680ea1d311ebb2dae116b8bdb084.json"
#       },
#       "ScalingPolicy": {
#         "InvocationsPerInstance": 240,
#         "MinCapacity": 2,
#         "MaxCapacity": 10
#       },
#       "TestDataset": {
#         "Bucket": "ml-serving-perftest",
#         "Key": "_data/tweet-sentiments/tweet-sentiments/dataset.csv"
#       },
#       "JobDetails": {
#         "ExecutionId": "bd0e680ea1d311ebb2dae116b8bdb084",
#         "ClusterName": "ml-serving",
#         "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/locust-load-test:3",
#         "AwsRegion": "ap-southeast-1",
#         "Subnets": [
#           "subnet-55476b32",
#           "subnet-7581dc3c"
#         ],
#         "SecurityGroups": [
#           "sg-01044b90c2c0ad58e"
#         ],
#         "FamilyName": "locust-load-test",
#         "MasterTaskName": "locust-load-test",
#         "MasterCommand": [
#           "python3",
#           "driver.py",
#           "--host",
#           "https://zgr57hqpad.execute-api.ap-southeast-1.amazonaws.com/api/performance/",
#           "--client-type",
#           "master",
#           "--expected-workers",
#           "1",
#           "--master-host",
#           "0.0.0.0",
#           "--shapes-bucket",
#           "ml-serving-perftest",
#           "--shapes-key",
#           "_loadtest/shapes/bd0e680ea1d311ebb2dae116b8bdb084.json",
#           "--output-bucket",
#           "ml-serving-perftest",
#           "--output-key",
#           "_loadtesting/2021-04-20/bd0e680ea1d311ebb2dae116b8bdb084.json"
#         ]
#       },
#       "Jobs": [
#         {
#           "EndpointName": "loadtesting-dddd-0",
#           "ExecutionId": "bd0e680ea1d311ebb2dae116b8bdb084",
#           "ClusterName": "ml-serving",
#           "TaskDefinition": "arn:aws:ecs:ap-southeast-1:908177370303:task-definition/locust-load-test:3",
#           "AwsRegion": "ap-southeast-1",
#           "Subnets": [
#             "subnet-55476b32",
#             "subnet-7581dc3c"
#           ],
#           "SecurityGroups": [
#             "sg-01044b90c2c0ad58e"
#           ],
#           "FamilyName": "locust-load-test",
#           "TestDataset": {
#             "Bucket": "ml-serving-perftest",
#             "Key": "_data/tweet-sentiments/tweet-sentiments/dataset.csv"
#           },
#           "WorkerTaskName": "locust-load-test",
#           "WorkerCommand": [
#             "python3",
#             "driver.py",
#             "--host",
#             "https://zgr57hqpad.execute-api.ap-southeast-1.amazonaws.com/api/performance/",
#             "--client-type",
#             "worker",
#             "--shapes-bucket",
#             "ml-serving-perftest",
#             "--shapes-key",
#             "_loadtest/shapes/bd0e680ea1d311ebb2dae116b8bdb084.json"
#           ]
#         }
#       ]
#     }
#   ]
# }
# handler(event, {})