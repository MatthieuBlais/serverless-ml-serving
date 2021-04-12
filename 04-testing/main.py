from client import APIClient


def api_testing(host, testcases_bucket, testcases_key, result_bucket, result_key):
    api = APIClient(host)
    api.run_tests(bucket, key)
    api.upload_report(result_bucket, result_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "-H")
    parser.add_argument("--testcases-bucket", default=None)
    parser.add_argument("--testcases-key", default=None)
    parser.add_argument("--result-bucket", default=None)
    parser.add_argument("--result-key", default=None)
    args = parser.parse_args()

    print(f"Configuration: host={args.host}, protocol-bucket={args.protocol_bucket}, protocol-key={args.protocol_key}")
    api_testing(args.host, args.protocol_bucket, args.protocol_key)

