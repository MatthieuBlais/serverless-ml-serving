import matplotlib.pyplot as plt
from io import BytesIO
import os
import boto3

s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))


class Graph():

    @classmethod
    def generate_graph(cls, labels, series, bucket=None, key=None):
        plt.figure(figsize=(15, 15))
        for idx, label in enumerate(labels):
            y = series[idx]
            x = [i*5 for i in range(len(series[idx]))]
            plt.plot(x, y, label=label)
        plt.xlabel('duration (s)')
        plt.ylabel('response time (ms)')
        plt.title('Load testing')
        plt.legend()
        img_data = BytesIO()
        plt.savefig(img_data, format='png')
        img_data.seek(0)
        if bucket:
            return cls.upload_graph(bucket, key, img_data)
        return img_data


    @classmethod
    def upload_graph(cls, bucket, key, plot):
        s3.put_object(Bucket=bucket, Key=key, Body=plot, ContentType='image/png')
        return {
            "Bucket": bucket,
            "Key": key
        }