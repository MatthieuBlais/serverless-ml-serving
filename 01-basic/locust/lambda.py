from locust import task, between, HttpUser
from locust.contrib.fasthttp import FastHttpUser
import csv
import json

ENDPOINT_NAME = "/dev/sentiments/tweet/lambda"
JSON_HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}
TEST_DATA_PATH = "../model/data/test.csv"

# locust -f lambda.py --headless -u 10 -r 5 -t 5m --host https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com

class LambdaInterface(HttpUser):
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


# 1 MIN

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet/lambda                                       56     61     65     74     88     97    110    120    360    360    360    382
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         56     61     65     74     88     97    110    120    360    360    360    382


# 10 MIN

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet/lambda                                       50     53     56     59     70     86    130    190    350    640    640   3857
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         50     53     56     59     70     86    130    190    350    640    640   3857


# 5 MIN - UserHTPP

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet/lambda                                       51     54     57     60     70     79    110    200    680    720    720   1914
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         51     54     57     60     70     79    110    200    680    720    720   1914


# Cold and slow

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet/lambda                                       55     59     61     62     68     78    760   1200   1400   1400   1400    160
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         55     59     61     62     68     78    760   1200   1400   1400   1400    160

# EDGE

# Response time percentiles (approximated)
#  Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  POST     /dev/sentiments/tweet/lambda                                       57     61     65     71     90    130    230    330   1100   1200   1200   1919
# --------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
#  None     Aggregated                                                         57     61     65     71     90    130    230    330   1100   1200   1200   1919