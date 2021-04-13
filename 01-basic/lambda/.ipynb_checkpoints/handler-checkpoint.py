import json
import boto3

sagemaker = boto3.client('sagemaker-runtime')
ENDPOINT_NAME = 'tensorflow-inference-2021-03-22-13-42-55-037'

def handler(event, context):
    print("New event", json.dumps(event['body']))
    response = {}
    http_response = {}
    try:
        result = sagemaker.invoke_endpoint(EndpointName=ENDPOINT_NAME, Body=event['body'])
        response = json.loads(result['Body'].read())
        http_response = {
            'statusCode': 200,
            'body': json.dumps({
                "sentiment": {
                    "label": "positive" if response["predictions"][0][0]>=0.5,
                    "score": response["predictions"][0][0]
                }
            }),
            'headers':{
                'Content-Type':'application/json',
                'Access-Control-Allow-Origin':'*'
            }
        }
    except Exception as e:
        http_response = {
            'statusCode': 500,
            'body': json.dumps(response),
            'headers':{
                'Content-Type':'application/json',
                'Access-Control-Allow-Origin':'*'
            }
        }
    print("Response", json.dumps(response))
    return http_response