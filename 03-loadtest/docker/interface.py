from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
import csv
import json
import sys
import boto3
import os
from locust import LoadTestShape

os.environ["AWS_REGION"] = "ap-southeast-1"
os.environ["ENDPOINT_NAME"] = "/dev/sentiments/tweet"
os.environ["TEST_DATASET_BUCKET"] = "ml-serving-perftest"
os.environ["TEST_DATASET_KEY"] = "_data/tweet-sentiments/tweet-sentiments/dataset.csv"


class StagesShape(LoadTestShape):
    """
    A simply load test shape class that has different user and spawn_rate at
    different stages.
    Keyword arguments:
        stages -- A list of dicts, each representing a stage with the following keys:
            duration -- When this many seconds pass the test is advanced to the next stage
            users -- Total user count
            spawn_rate -- Number of users to start/stop per second
            stop -- A boolean that can stop that test at a specific stage
        stop_at_end -- Can be set to stop once all stages have run.
    """
    time_limit = 600
    spawn_rate = 20
    stop_at_end = True

    stages = [
        {"duration": 30, "users": 100, "spawn_rate": 100},
        {"duration": 60, "users": 150, "spawn_rate": 100},
        {"duration": 90, "users": 200, "spawn_rate": 100},
        {"duration": 120, "users": 130, "spawn_rate": 100},
        {"duration": 150, "users": 310, "spawn_rate": 100},
        {"duration": 180, "users": 100, "spawn_rate": 100},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None


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