import gevent
from interface import APIInterface
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
import argparse
import datetime
import boto3
import os
import json

setup_logging("INFO", None)
s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])

def save_results(bucket, key, results):
    """Save output to S3"""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(results)
    )

def load_testing(users, spawn_rate, run_time, host, output_bucket=None, output_key=None):
    # setup Environment and Runner
    env = Environment(user_classes=[APIInterface])
    env.host = host
    env.create_local_runner()

    # start a greenlet that periodically outputs the current stats
    gevent.spawn(stats_printer(env.stats))

    # start a greenlet that save current stats to history
    gevent.spawn(stats_history, env.runner)

    # start the test
    env.runner.start(users, spawn_rate)

    # in run_time seconds stop the runner
    gevent.spawn_later(run_time, lambda: env.runner.quit())

    # wait for the greenlets
    env.runner.greenlet.join()

    results = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "current_rps": env.stats.total.current_rps or 0,
        "current_fail_per_sec": env.stats.total.current_fail_per_sec or 0,
        "min_response_time": env.stats.total.min_response_time,
        "max_response_time": env.stats.total.max_response_time,
        "response_time_percentile_999": env.stats.total.get_current_response_time_percentile(0.99) or 0,
        "response_time_percentile_99": env.stats.total.get_current_response_time_percentile(0.99) or 0,
        "response_time_percentile_95": env.stats.total.get_current_response_time_percentile(0.95) or 0,
        "response_time_percentile_90": env.stats.total.get_current_response_time_percentile(0.90) or 0,
        "response_time_percentile_80": env.stats.total.get_current_response_time_percentile(0.80) or 0,
        "response_time_percentile_75": env.stats.total.get_current_response_time_percentile(0.75) or 0,
        "response_time_percentile_66": env.stats.total.get_current_response_time_percentile(0.66) or 0,
        "response_time_percentile_50": env.stats.total.get_current_response_time_percentile(0.5) or 0,
        "user_count": env.runner.user_count or 0,
        "num_requests": env.stats.total.num_requests
    }
    print(results)
    if output_bucket:
        save_results(output_bucket, output_key, results)

# locust -f apigateway.py --headless -u 10 -r 5 -t 5m --host https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", "-u", type=int, default=5)
    parser.add_argument("--spawn-rate", "-r", type=int, default=5)
    parser.add_argument("--run-time", "-t", type=int, default=5)
    parser.add_argument("--host", "-H")
    parser.add_argument("--output-bucket", default=None)
    parser.add_argument("--output-key", default=None)
    args = parser.parse_args()
    load_testing(args.users, args.spawn_rate, args.run_time, args.host)


    