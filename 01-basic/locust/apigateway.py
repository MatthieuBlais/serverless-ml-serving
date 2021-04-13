from locust import task, between
from locust.contrib.fasthttp import FastHttpUser
import csv
import json

ENDPOINT_NAME = "/dev/sentiments/tweet"
JSON_HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}
TEST_DATA_PATH = "../model/data/test.csv"
RESULT_PATH = "stats/result_stats.csv"

# locust -f apigateway.py --headless -u 10 -r 5 -t 5m --host https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com

class LambdaInterface(FastHttpUser):
    endpoint_name = ENDPOINT_NAME
    wait_time = between(1, 2)

    @task
    def index(self):
        response = self.client.post(self.endpoint_name, data=json.dumps({"tweet": self.tweets[self.tweet_idx]}), headers=JSON_HEADERS)
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


    def on_stop(self):
        """Save the results to S3"""
        print("STOPPING")
        results = {}
        with open(RESULT_PATH, "r") as f:
            reader = csv.reader(f, delimiter=",")
            headers = next(reader)
            data = next(reader)
            for header, value in zip(headers, data):
                results[header] = value
        print(json.dumps(results, indent=4))
        with open("stats/jss.json", "w+") as f:
            json.dump(results, f)

# 1 MIN

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet                                              67     80     86     89    100    110    130    130    190    190    190    375
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         67     80     86     89    100    110    130    130    190    190    190    375


# 10 MIN

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet                                              46     50     54     56     68     88    140    200    320    450    450   3862
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         46     50     54     56     68     88    140    200    320    450    450   3862


# Cold and slow


# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet                                              77     82     87     89    100    120    270    310    380    380    380    176
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         77     82     87     89    100    120    270    310    380    380    380    176


# SLOW EDGE

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet                                              58     75     82     84     93    120    150    190    210    210    210    171
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         58     75     82     84     93    120    150    190    210    210    210    171


# Ok EDGE

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet                                              48     53     57     60     74     86    120    170    390    560    560   1934
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         48     53     57     60     74     86    120    170    390    560    560   1934