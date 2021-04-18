FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV AWS_REGION=ap-southeast-1
ENV AWS_ACCESS_KEY_ID=AKIA5G44W5S7VPKVALFW
ENV AWS_SECRET_ACCESS_KEY=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


CMD ["python3", "driver.py"]