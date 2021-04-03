from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
import csv
import json
import sys
import boto3
import os


class APIInterface(FastHttpUser):

    s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])
    endpoint_name = os.environ["ENDPOINT_NAME"]
    headers = {'Content-Type': os.environ.get("CONTENT_TYPE", 'application/json'), 'Accept': 'application/json'}
    wait_time = between(1, 2)

    @task
    def index(self):
        response = self.client.post(self.endpoint_name, data=self.testdata[self.data_idx], headers=self.headers)
        self.data_idx += 1
        if self.data_idx == self.total_data:
            self.data_idx = 0

    def on_start(self):
        """Trigger when locust start"""
        dataset = self.download_test_set()
        self.testdata = []
        self.testexpected = []
        reader = csv.reader(dataset, delimiter=",")
        next(reader)
        for row in reader:
            self.testdata.append(row[0])
            # if len(row)>1:
            #     self.testexpected.append(json.loads(row[1]))
        self.total_data = len(self.testdata)
        self.data_idx = 0
        
    def download_test_set(self):
        """Download test set from S3"""
        obj = self.s3.get_object(Bucket=os.environ["TEST_DATASET_BUCKET"], Key=os.environ["TEST_DATASET_KEY"])
        return obj["Body"].read().decode().split()