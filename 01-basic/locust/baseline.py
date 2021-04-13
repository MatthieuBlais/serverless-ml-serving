import boto3
import json
import time
from locust import User, between, task
import csv

TEST_DATA_PATH = "../model/data/test.csv"
ENDPOINT_NAME = "tweet-sentiments"

# locust -f baseline.py --headless -u 10 -r 5 -t 10m

class SageMakerClient():
    """
    Simple SageMaker invocation using boto3 wrapper and implementing locust events to collect statistics
    """

    _locust_environment = None

    def __init__(self, endpoint_name):
        self.client = boto3.client("sagemaker-runtime" )
        self.endpoint_name = endpoint_name

    @classmethod
    def total_time(cls, start_time):
        return int((time.time() - start_time) * 1000)

    def invoke(self, tweet):
        start_time = time.time()
        try:
            self.client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                Body=tweet
            )
        except Exception as e:
            self._locust_environment.events.request_failure.fire(
                request_type="execute",
                name=self.endpoint_name,
                response_time=self.total_time(start_time),
                response_length=0,
                exception=e
            )
        self._locust_environment.events.request_success.fire(
            request_type="execute",
            name=self.endpoint_name,
            response_time=self.total_time(start_time),
            response_length=0
        )


class SageMakerUser(User):
    """
    Abstract user class to register SageMaker client
    """

    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = SageMakerClient(self.endpoint_name)
        self.client._locust_environment = self.environment


class ApiUser(SageMakerUser):
    endpoint_name = ENDPOINT_NAME
    wait_time = between(1, 2)

    @task
    def invoke_endpoint(self):
        self.client.invoke(self.tweets[self.tweet_idx])
        self.tweet_idx += 1
        if self.tweet_idx == self.total_tweets:
            self.tweet_idx = 0


    def on_start(self):
        self.tweets = []
        with open(TEST_DATA_PATH, "r") as f:
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                self.tweets.append(row[0])
        self.total_tweets = len(self.tweets)
        self.tweet_idx = 0



# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  execute  tweet-sentiments                                                   61     65     69     72     84     96    120    180    370    420    420   3820
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         61     65     69     72     84     96    120    180    370    420    420   3820