FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

ENV AWS_REGION=ap-southeast-1
ENV AWS_ACCESS_KEY_ID=AKIA5G44W5S72HSQNFOV
ENV AWS_SECRET_ACCESS_KEY=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


CMD ["python3", "driver.py"]