






if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "-H")
    parser.add_argument("--protocol-bucket", default=None)
    parser.add_argument("--protocol-key", default=None)
    args = parser.parse_args()

    print(f"Configuration: host={args.host}, protocol-bucket={args.protocol_bucket}, protocol-key={args.protocol_key}")
    api_testing(args.host, args.protocol_bucket, args.protocol_key)

