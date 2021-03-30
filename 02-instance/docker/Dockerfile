FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV AWS_REGION=ap-southeast-1
ENV ENDPOINT_NAME=/dev/sentiments/tweet
ENV TEST_DATASET_BUCKET=sagemaker-ap-southeast-1-908177370303
ENV TEST_DATASET_KEY=locust/tweet-sentiments/test.csv


CMD ["python3", "driver.py"]