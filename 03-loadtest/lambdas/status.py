import boto3
import os
import json

client = boto3.client('ecs', region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))

def filter_tasks(tasks, task_name, execution_id):
    for task in tasks:
        if task['overrides']['containerOverrides'][0]['name'] == task_name:
            for env in task['overrides']['containerOverrides'][0]['environment']:
                if env['name'] == 'EXECUTION_ID' and env['value'] == execution_id:
                    return task
    return None

def extract_private_ip(task):
    for x in task['attachments']:
        if x['type'] == 'ElasticNetworkInterface':
            for det in x['details']:
                if det['name'] == 'privateIPv4Address':
                    return det['value']
    return None

def inject_attributes_in_workers(workers, ip_address, task_arn):
    params = [
        "--master-host",
        ip_address,
        "--fargate-task",
        task_arn
    ]
    for i in range(len(workers)):
        workers[i]["WorkerCommand"] += params
    return workers

def handler(event, context):

    print(json.dumps(event))

    loop = True
    response = {}
    while loop:
        params = {
            'cluster': event["JobDetails"]["ClusterName"],
            'family': event["JobDetails"]["FamilyName"],
        }
        if response.get('nextToken'):
            params['nextToken'] = response.get('nextToken')
        
        response = client.list_tasks(**params)

        if len(response['taskArns']) == 0:
            event['MasterStatus'] = 'STOPPED'
            break
        task_descriptions = client.describe_tasks(
            cluster=event["JobDetails"]["ClusterName"],
            tasks=response['taskArns']
        )
        task = filter_tasks(task_descriptions['tasks'], event["JobDetails"]["MasterTaskName"], event["JobDetails"]["ExecutionId"])
        print(task)
        if task is None and not response.get("nextToken"):
            event['MasterStatus'] = 'STOPPED'
            loop = False
        elif task:
            event["MasterStatus"] = task['lastStatus']
            event['MasterTaskArn'] = task['taskArn']
            event['MasterPrivateIp'] = extract_private_ip(task)
            event['Jobs'] = inject_attributes_in_workers(event['Jobs'], event['MasterPrivateIp'], event['MasterTaskArn'])
            loop = False

    return event
        


# event = {
#     "JobDetails": {
#         "ExecutionId": "ddd",
#         "ClusterName": "ml-serving",
#         "FamilyName": "locust-load-test",
#         "MasterTaskName": "locust-load-test",
#         "Jobs": []
#     }
# }
# print(handler(event, {}))