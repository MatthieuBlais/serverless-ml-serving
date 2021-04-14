import gevent
from interface import APIInterface, StagesShape
from locust.env import Environment
from locust.stats import stats_printer, HISTORY_STATS_INTERVAL_SEC
from locust.log import setup_logging
import argparse
import datetime
import boto3
import os
import json

setup_logging("INFO", None)
s3 = boto3.client('s3', region_name=os.environ["AWS_REGION"])


def stats_history(runner, percentiles=["50","95"]):
    """Save current stats info to history for charts of report."""
    while True:
        stats = runner.stats
        if not stats.total.use_response_times_cache:
            break
        if runner.state != "stopped":
            r = {
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "current_rps": stats.total.current_rps or 0,
                "current_fail_per_sec": stats.total.current_fail_per_sec or 0,
                "user_count": runner.user_count or 0,
            }
            for percentile in percentiles:
                pvalue = float(percentile) / (10**len(percentile))
                r[f"response_time_percentile_{percentile}"] = stats.total.get_current_response_time_percentile(pvalue) or 0
            stats.history.append(r)
        gevent.sleep(HISTORY_STATS_INTERVAL_SEC)


def save_results(bucket, key, results):
    """Save output to S3"""
    existing = []
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        existing = json.loads(obj['Body'].read())
    except Exception:
        existing = []
    existing.append(results)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(existing)
    )

def load_testing(run_time, host, output_bucket=None, output_key=None, percentiles="50,95"):
    
    # setup Environment and Runner
    env = Environment(user_classes=[APIInterface], shape_class=StagesShape())
    env.host = host
    env.create_local_runner()

    # start a greenlet that periodically outputs the current stats
    gevent.spawn(stats_printer(env.stats))

    # start a greenlet that save current stats to history
    gevent.spawn(stats_history, env.runner, percentiles.split(","))

    # start the test
    env.runner.start_shape()

    # in run_time seconds stop the runner
    gevent.spawn_later(run_time, lambda: env.runner.quit())

    # wait for the greenlets
    env.runner.greenlet.join()

    results = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "min_response_time": env.stats.total.min_response_time,
        "max_response_time": env.stats.total.max_response_time,
        "num_requests": env.stats.total.num_requests,
        "history": env.stats.history
    }
    for percentile in percentiles.split(","):
        pvalue = float(percentile) / (10**len(percentile))
        results[f"response_time_percentile_{percentile}"] = env.stats.total.get_current_response_time_percentile(pvalue) or 0

    print(results)
    if output_bucket:
        save_results(output_bucket, output_key, results)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-time", "-t", type=int, default=5)
    parser.add_argument("--host", "-H")
    parser.add_argument("--output-bucket", default=None)
    parser.add_argument("--output-key", default=None)
    parser.add_argument("--percentiles", default="50,95")
    args = parser.parse_args()

    print(f"Configuration: run-time={args.run_time}, host={args.host}, output=s3://{args.output_bucket}/{args.output_key}, percentiles={args.percentiles}")
    load_testing(args.run_time, args.host, args.output_bucket, args.output_key, args.percentiles)


# python driver.py --users 5 --spawn-rate 5 --run-time 20 --host https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com 