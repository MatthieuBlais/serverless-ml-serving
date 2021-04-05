

docker build . -t locust-test

aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 908177370303.dkr.ecr.ap-southeast-1.amazonaws.com

docker images

docker tag 4f099990c52d 908177370303.dkr.ecr.ap-southeast-1.amazonaws.com/ml-serving/locust-perftest

docker push 908177370303.dkr.ecr.ap-southeast-1.amazonaws.com/ml-serving/locust-perftest