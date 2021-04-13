from client import APIClient
import argparse

def api_testing(host, testcases_bucket, testcases_key, result_bucket, result_key):
    api = APIClient(host)
    api.run_tests(testcases_bucket, testcases_key)
    api.upload_report(result_bucket, result_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "-H")
    parser.add_argument("--testcases-bucket", default=None)
    parser.add_argument("--testcases-key", default=None)
    parser.add_argument("--result-bucket", default=None)
    parser.add_argument("--result-key", default=None)
    args = parser.parse_args()

    print(f"Configuration: host={args.host}, testcases-bucket={args.testcases_bucket}, testcases-key={args.testcases_key}")
    api_testing(args.host, args.testcases_bucket, args.testcases_key, args.result_bucket, args.result_key)



# python main.py --host https://uoykcmsezg.execute-api.ap-southeast-1.amazonaws.com 