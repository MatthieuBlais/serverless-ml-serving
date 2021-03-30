from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
import csv
import json
import sys
import boto3
import os

RESULT_PATH = "results/result_stats.csv"
# TEST_DATA_PATH = "../../01-basic/model/data/test.csv"
JSON_HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}


class APIInterface(FastHttpUser):

    s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])
    endpoint_name = os.environ["ENDPOINT_NAME"]
    wait_time = between(1, 2)

    @task
    def index(self):
        response = self.client.post(self.endpoint_name, data=json.dumps({"tweet": self.tweets[self.tweet_idx]}), headers=JSON_HEADERS)
        self.tweet_idx += 1
        if self.tweet_idx == self.total_tweets:
            self.tweet_idx = 0

    def on_start(self):
        """Trigger when locust start"""
        # self.tweets = []
        # with open(TEST_DATA_PATH, "r") as f:
        #     reader = csv.reader(f, delimiter=",")
        #     next(reader)
        #     for row in reader:
        #         self.tweets.append(row[0])
        # self.total_tweets = len(self.tweets)
        # self.tweet_idx = 0
        dataset = self.download_test_set()
        self.tweets = []
        reader = csv.reader(dataset, delimiter=",")
        next(reader)
        for row in reader:
            self.tweets.append(row[0])
        self.total_tweets = len(self.tweets)
        self.tweet_idx = 0
        
    def download_test_set(self):
        """Download test set from S3"""
        obj = self.s3.get_object(Bucket=os.environ["TEST_DATASET_BUCKET"], Key=os.environ["TEST_DATASET_KEY"])
        return obj["Body"].read().decode().split()