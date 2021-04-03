


aws ecr get-login-password --region region | docker login --username AWS --password-stdin accountid.dkr.ecr.region.amazonaws.com

docker build . -t accountid.dkr.ecr.region.amazonaws.com/ml-serving/locust-perftest

docker push accountid.dkr.ecr.region.amazonaws.com/ml-serving/locust-perftest